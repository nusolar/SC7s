from typing import cast
from time import sleep
from threading import Thread, Lock
from pathlib import Path
from copy import deepcopy

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from digi.xbee.devices import XBeeDevice
import serial
import json

from src import ROOT_DIR, BUFFERED_XBEE_MSG_END
from src.can.row import Row
from src.util import add_dbc_file, find, unwrap
from src.can_db import SQLiteEngine

import src.car_gui as car_display
import src.can_db as can_db

CAN_INTERFACE = "textfile" #canusb, pican, textfile

VIRTUAL_BUS_NAME = "virtbus"

XBEE_PORT = "/dev/ttyUSB0"
XBEE_BAUD_RATE = 57600
REMOTE_NODE_ID = "Router"

SERIAL_PORT = "COM9"
SERIAL_BAUD_RATE = 500000

MOCK_DATA_FILE = ROOT_DIR.parent.joinpath("example-data", "testInputRaw.txt")

xbee = None
remote = None
store_data = True
should_send = False
should_display = False

# Thread communication globals
row_lock = Lock()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc")))
# add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "mppt.dbc"))
# add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms_altered.dbc"))

if store_data:
    # Connection
    engine = SQLiteEngine(ROOT_DIR.joinpath("resources", "mock_candata2.db"))
    conn = can_db.connect(engine)

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

# made this it's own function because how you store the mock data could change
def parseTextFileLine(line):
    line = line.replace("\'", "\"")
    raw = json.loads(line)
    tag = raw["id"]
    data = bytearray.fromhex(raw["data"])

    return tag, data

def get_packets(interface) -> iter:
    """Generates CAN Packets."""
    if interface == 'canusb':
        with serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE) as receiver:
            while(True):
                raw = receiver.read_until(b';').decode()
                if len(raw) != 23: continue
                raw = raw[1:len(raw) - 1]
                raw = raw.replace('S', '')
                raw = raw.replace('N', '')
                tag = int(raw[0:3], 16)
                data = bytearray.fromhex(raw[3:])
                sleep(.1)
                yield can.Message(arbitration_id=tag, data=data)
    elif interface == 'pican':
        with can.interface.Bus(channel='can0', bustype='socketcan') as bus:
            for msg in bus:
                tag = msg.arbitration_id
                data = msg.data
                yield can.Message(arbitration_id=tag, data=data)
    elif interface == 'textfile':
        with open(MOCK_DATA_FILE, 'r') as receiver:
            bus = receiver.readlines()
            for msg in bus:
                (tag, data) = parseTextFileLine(msg)
                sleep(.1)
                yield can.Message(arbitration_id=tag, data=data)
    else:
        raise Exception('Invalid interface')

def row_accumulator_worker(bus: can.ThreadSafeBus):
    global car_display
    """
    Observes messages sent on the `bus` and accumulates them in a global row.
    """
    for msg in get_packets(CAN_INTERFACE):
        assert msg is not None

        row = find(rows, lambda r: r.owns(msg, db))
        if row is not None:
            row = unwrap(row)

            # i = next(i for i, r in enumerate(rows) if r.owns(msg, db))
            decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
            with row_lock:
                for k, v in decoded.items():
                    row.signals[k].update(v)
                    if k in car_display.displayables.keys():
                        car_display.displayables[k] = v
                        # print(car_display.displayables)

        
        # decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
        # with row_lock:
        #     for k, v in decoded.items():
        #         rows[i].signals[k].update(v)


# TODO: Buffering sucks. Get rid of the need for this (with more space-efficient serialization).
def buffered_payload(payload: str, chunk_size: int = 256, terminator: str = BUFFERED_XBEE_MSG_END) -> list[str]:
        payload += terminator
        return [payload[i:i + chunk_size] for i in range(0, len(payload), chunk_size)]

def sender_worker():
    """
    Serializes rows into the queue.
    """
    while True:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            row.stamp()
            if store_data:
                can_db.add_row(conn, row.timestamp, row.signals.values(), row.name, engine)
            for chunk in buffered_payload(row.serialize()):
                print(chunk)
                print("\n")
                if should_send:
                    xbee.send_data(remote, chunk)

def startXbee():
    global xbee, remote
    xbee = XBeeDevice(XBEE_PORT, XBEE_BAUD_RATE)
    xbee.open()

    remote = xbee.get_network().discover_device(REMOTE_NODE_ID)
    assert remote is not None


#displays the car gui, receives can data, stores it, and sends it over the xbees
if __name__ == "__main__":
    if should_send:
        startXbee()
    if store_data:
        for row in rows:
            can_db.create_tables(conn, row.name, row.signals.items(), engine)
        print("ready to receive")
    # Start the bus
    # Create a thread to read of the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(channel='virtbus', bustype='virtual'),),
                         daemon=True)

    # # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    # Start the threads
    accumulator.start()
    sender.start()

    #display
    if should_display:
        root = car_display.CarDisplay()
        root.mainloop()

    # Spin forever.
    while True: ...
