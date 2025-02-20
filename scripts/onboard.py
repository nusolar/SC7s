from typing import cast, generator, optional
from time import sleep
from threading import thread, lock
from copy import deepcopy
from dataclasses import dataclass
import argparse
from pathlib import path
from datetime import datetime
from queue import queue
import pynmea2

import can
import cantools.database
from cantools.database.can.database import database
from cantools.typechecking import signaldicttype
from digi.xbee.devices import xbeedevice
import serial
import json

from sqlalchemy import url, create_engine
from sqlalchemy.orm import session


from src import root_dir
from src.can.row import row
from src.util import add_dbc_file, find
import src.gui
import src.sql

gps_port = "/dev/ttyama0"
#maybe 0
xbee_port = "/dev/ttyusb0"
xbee_baud_rate = 57600
remote_node_id = "router"

serial_port = "com9"
serial_baud_rate = 500000

mock_data_file = root_dir.parent.joinpath("example-data", "testinputraw.txt")

xbee = none
remote = none

# thread communication globals
row_lock = lock()

# the database used for parsing with cantools
db = cast(database, cantools.database.load_file(root_dir.joinpath("resources", "mppt.dbc")))
add_dbc_file(db, root_dir.joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, root_dir.joinpath("resources", "bms_altered.dbc"))
add_dbc_file(db, root_dir.joinpath("resources", "driver_controls.dbc"))

parser = argparse.argumentparser()

parser.add_argument("--store", action=argparse.booleanoptionalaction, default=true)
parser.add_argument("--send", action=argparse.booleanoptionalaction, default=true)
parser.add_argument("--display", action=argparse.booleanoptionalaction, default=true)
parser.add_argument(
    "--db-url",
    type=str,
    default=str(
        url.create(drivername="sqlite",database=str(root_dir.joinpath("resources", "can_sending.db")))
    )
)
parser.add_argument("--serial-port", type=str)
parser.add_argument("--serial-baud-rate", type=str)
parser.add_argument("--xbee-port", type=str)
parser.add_argument("--xbee-baud-rate", type=int)
parser.add_argument("--remote-node-id", type=str)

args = parser.parse_args()

session = session(create_engine(args.db_url)) if args.store else none

# the rows that will be added to the database
rows = [row(db, node.name) for node in db.nodes]

@dataclass
class canusbinterface:
    serial_port: str
    baud_rate: int

@dataclass
class picaninterface:
    channel: str = "can0"
    bustype: str = "socketcan"

@dataclass
class textfileinterface:
    file: path

@dataclass
class gpsdata:
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float
    course: float

    def serialize(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'lat': self.latitude,
            'lon': self.longitude,
            'speed': self.speed,
            'course': self.course,
        }

class gpsreader:
    def __init__(self,port = gps_port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial = none
    def connect(self):
        try:
            self.serial = serial.serial(
                    port = self.port,
                    baudrate = self.baud_rate,
                    timeout=1,
            )
            return true
        except serial.serialexception as e:
            print(e)
            return false

    def read_gps(self):
        if self.serial is none or not self.serial.is_open:
            res = self.connect()
            if not res:
                print("bad connection")
                return none
        try:
            line = self.serial.readline().decode('ascii', errors='ignore').strip()
            if line.startswith('$'):
                return pynmea2.parse(line)
        except exception as e:
            print(f"gps error: {e}")
            return none

            

interface = canusbinterface | picaninterface | textfileinterface

# made this it's own function because how you store the mock data could change
def parse_text_file_line(line):
    line = line.replace("\'", "\"")
    raw = json.loads(line)
    tag = raw["id"]
    data = bytearray.fromhex(raw["data"])

    return tag, data

def get_packets(interface: interface) -> generator[can.message, none, none]:
    """generates can packets."""
    match interface:
        case canusbinterface(port, baud_rate):
            with serial.serial(port, baud_rate) as receiver:
                while(true):
                    raw = receiver.read_until(b';').decode()
                    if len(raw) != 23: continue
                    raw = raw[1:len(raw) - 1]
                    raw = raw.replace('s', '')
                    raw = raw.replace('n', '')
                    tag = int(raw[0:3], 16)
                    data = bytearray.fromhex(raw[3:])
                    yield can.message(arbitration_id=tag, data=data)

        case picaninterface(channel, bustype):
            with can.interface.bus(channel=channel, bustype=bustype) as bus: # type: ignore
                for msg in bus:
                    tag = msg.arbitration_id
                    data = msg.data
                    yield can.message(arbitration_id=tag, data=data)
        
        case textfileinterface(file):
            with file.open("r") as receiver:
                bus = receiver.readlines()
                for msg in bus:
                    (tag, data) = parse_text_file_line(msg)
                    sleep(.1)
                    yield can.message(arbitration_id=tag, data=data)

def gps_worker(gpsqueue : queue):
    reader = gpsreader()
    
    if not reader.connect():
        print("connection failed")
        return
    currdata = none

    while true:
        msg = reader.read_gps()
        if msg:
            try:
               if msg.sentence_type == 'rmc':
                        current_data = gpsdata(
                            timestamp=datetime.now(),
                            latitidude=msg.latitude,
                            longitude=msg.longitude,
                            speed=msg.spd_over_grnd * 1.852,  # knots to km/h
                            course=msg.true_course or 0.0,
                        )
                
               elif msg.sentence_type == 'gga' and current_data:
                        current_data.satellites = msg.num_satellites
                        current_data.fix_quality = msg.gps_qual
                        gps_queue.put(current_data)
                        current_data = none             
            except exception as e:
                print(f"{e}")

    
def row_accumulator_worker(interface: interface):
    """
    observes messages sent on the `bus` and accumulates them in a global row.
    """
    for msg in get_packets(interface):
        assert msg is not none

        row = find(rows, lambda r: r.owns(msg, db))
        if row is not none:
            decoded = cast(signaldicttype, db.decode_message(msg.arbitration_id, bytes(msg.data)))
            with row_lock:
                for k, v in decoded.items():
                    row.signals[k].update(v)
                    if k in src.gui.displayables.keys():
                        src.gui.displayables[k] = cast(float, v)
        else:
            print("????:", msg)

def sender_worker():
    """
    serializes rows into the queue.
    """
    if session is not none:
        for row in rows:
            src.sql.create_tables(session, row.name, row.signals.items())

    while true:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            row.stamp()
            if session is not none:
                src.sql.add_row(session, row)
            if xbee is not none:
                xbee.send_data(remote, row.serialize())

def start_xbee():
    global xbee, remote
    xbee = xbeedevice(xbee_port, xbee_baud_rate)
    xbee.open()

    remote = xbee.get_network().discover_device(remote_node_id)
    assert remote is not none

# displays the car gui, receives can data, stores it, and sends it over the xbees
if __name__ == "__main__":
    if session is not none:
        for row in rows:
            src.sql.create_tables(session, row.name, row.signals.items())

    print("====================ready====================")

    # create a thread to read off the bus and maintain the rows
    accumulator = thread(target=row_accumulator_worker,
                         args=(textfileinterface(path("testinputraw.txt")),),
                         daemon=true)
    gps_queue = queue()
    gps_thread = thread(target=gps_worker, args=(gps_queue,), daemon=true)

    # create a thread to serialize rows as would be necessary with xbees
    sender = thread(target=sender_worker, daemon=true)

    # start the threads
    accumulator.start()
    sender.start()
    gps_thread.start()

    # display
    if args.display:
        root = src.gui.cardisplay()
        root.mainloop()

    # spin forever.
    while true:
        input()
