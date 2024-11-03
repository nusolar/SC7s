from typing import cast, Generator
from time import sleep
from threading import Thread, Lock
from copy import deepcopy
from dataclasses import dataclass
import argparse
from pathlib import Path

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from digi.xbee.devices import XBeeDevice
import serial
import json

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session
import serial
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import ROOT_DIR, BUFFERED_XBEE_MSG_END
from src.can.virtual import start_virtual_can_bus
from src.can.row import Row
from src.util import add_dbc_file, find
import src.car_gui as car_display
import src.can_db as can_db

XBEE_PORT = "/dev/ttyUSB0"
XBEE_BAUD_RATE = 57600
REMOTE_NODE_ID = "Router"

SERIAL_PORT = "COM9"
SERIAL_BAUD_RATE = 500000

MOCK_DATA_FILE = ROOT_DIR.parent.joinpath("example-data", "testInputRaw.txt")

xbee = None
remote = None

# Thread communication globals
row_lock = Lock()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(ROOT_DIR.joinpath("resources", "mppt.dbc")))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "bms_altered.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "driver_controls.dbc"))

parser = argparse.ArgumentParser()

parser.add_argument("--store", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--send", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--display", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument(
    "--db-url",
    type=str,
    default=str(
        URL.create(drivername="sqlite",database=str(ROOT_DIR.joinpath("resources", "can_sending.db")))
    )
)
parser.add_argument("--serial-port", type=str)
parser.add_argument("--serial-baud-rate", type=str)
parser.add_argument("--xbee-port", type=str)
parser.add_argument("--xbee-baud-rate", type=int)
parser.add_argument("--remote-node-id", type=str)

args = parser.parse_args()

session = Session(create_engine(args.db_url)) if args.store else None

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

@dataclass
class CanusbInterface:
    serial_port: str
    baud_rate: int

@dataclass
class PicanInterface:
    channel: str = "can0"
    bustype: str = "socketcan"

@dataclass
class TextFileInterface:
    file: Path

Inteface = CanusbInterface | PicanInterface | TextFileInterface

# made this it's own function because how you store the mock data could change
def parseTextFileLine(line):
    line = line.replace("\'", "\"")
    raw = json.loads(line)
    tag = raw["id"]
    data = bytearray.fromhex(raw["data"])

    return tag, data

def get_packets(interface: Inteface) -> Generator[can.Message, None, None]:
    """Generates CAN Packets."""
    match interface:
        case CanusbInterface(port, baud_rate):
            with serial.Serial(port, baud_rate) as receiver:
                while(True):
                    raw = receiver.read_until(b';').decode()
                    if len(raw) != 23: continue
                    raw = raw[1:len(raw) - 1]
                    raw = raw.replace('S', '')
                    raw = raw.replace('N', '')
                    tag = int(raw[0:3], 16)
                    data = bytearray.fromhex(raw[3:])
                    yield can.Message(arbitration_id=tag, data=data)

        case PicanInterface(channel, bustype):
            with can.ThreadSafeBus(car_display.VIRTUAL_BUS_NAME, bustype="virtual") as bus: # type: ignore
                for msg in bus:
                    tag = msg.arbitration_id
                    data = msg.data
                    yield can.Message(arbitration_id=tag, data=data)
        
        case TextFileInterface(file):
            with file.open("r") as receiver:
                bus = receiver.readlines()
                for msg in bus:
                    (tag, data) = parseTextFileLine(msg)
                    sleep(.1)
                    yield can.Message(arbitration_id=tag, data=data)

def row_accumulator_worker(interface: Inteface):
    """
    Observes messages sent on the `bus` and accumulates them in a global row.
    """
    for msg in get_packets(interface):
        assert msg is not None

        row = find(rows, lambda r: r.owns(msg, db))
        if row is not None:
            decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
            with row_lock:
                for k, v in decoded.items():
                    row.signals[k].update(v)
                    if k in car_display.displayables.keys():
                        car_display.displayables[k] = cast(float, v)
        else:
            print("????:", msg)

def sender_worker():
    """
    Serializes rows into the queue.
    """
    if session is not None:
        for row in rows:
            can_db.create_tables(session, row.name, row.signals.items())

    while True:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            row.stamp()
            can_db.add_row(session, row)
            if xbee is not None:
                xbee.send_data(remote, row.serialize())

def startXbee():
    global xbee, remote
    xbee = XBeeDevice(XBEE_PORT, XBEE_BAUD_RATE)
    xbee.open()

    remote = xbee.get_network().discover_device(REMOTE_NODE_ID)
    assert remote is not None

# Displays the car gui, receives can data, stores it, and sends it over the xbees
if __name__ == "__main__":
    if session is not None:
        for row in rows:
            can_db.create_tables(session, row.name, row.signals.items())

    print("====================Ready====================")

    # Create a thread to read off the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(PicanInterface(),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    # Start the threads
    accumulator.start()
    sender.start()

    start_virtual_can_bus(can.ThreadSafeBus(car_display.VIRTUAL_BUS_NAME, bustype="virtual"), db)

    # Display
    if args.display:
        root = car_display.CarDisplay()
        root.mainloop()

    # Spin forever.
    while True: ...
