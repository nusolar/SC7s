from typing import cast, Generator
from time import sleep
from threading import Thread, Lock
from copy import deepcopy
from dataclasses import dataclass
import argparse
from pathlib import Path
from queue import Queue

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

from src import ROOT_DIR
from src.can.row import Row
from src.util import add_dbc_file, find
import src.gui
import src.sql

# GPS-specific imports
import gps
import pynmea2
import asyncio


XBEE_PORT = "/dev/ttyUSB0"
XBEE_BAUD_RATE = 57600
REMOTE_NODE_ID = "Router"

SERIAL_PORT = "COM9"
SERIAL_BAUD_RATE = 500000

MOCK_DATA_FILE = ROOT_DIR.parent.joinpath("example-data", "testInputRaw.txt")

# Xbee and GPS globals
xbee = None
remote = None
gps_device = None

# Thread communication globals
row_lock = Lock()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(ROOT_DIR.joinpath("resources", "mppt.dbc")))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "bms_altered.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "driver_controls.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "gps.dbc")) #gps also has dbc file

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

@dataclass # how to parse GPS data, we had to write a class for this because there are no high level libraries for it
class GPSInterface:
    port: str
    baud_rate: int = 9600
    timeout: float = 0.5
    ser: Optional[serial.Serial] = None  # Will be initialized when instance is created

    def __post_init__(self):
        """Initialize the serial connection."""
        try:
            self.ser = serial.Serial(self.port, baudrate=self.baud_rate, timeout=self.timeout)
            if self.ser.is_open:
                print(f"Successfully connected to GPS on {self.port}")
        except serial.SerialException as e:
            print(f"Error opening GPS device on {self.port}: {e}")
    
    async def get_packets(self) -> AsyncGenerator[can.Message, None]:
        """Generates CAN Packets from GPS data asynchronously."""
        while True:
            # Read data asynchronously from the serial connection
            newdata = await asyncio.to_thread(self.ser.readline)  # Use asyncio.to_thread to run in background
            newdata = newdata.strip().decode("unicode-escape")
            
            if newdata.startswith("$GNRMC"):
                try:
                    newmsg = pynmea2.parse(newdata)
                    lat = newmsg.latitude
                    lng = newmsg.longitude
                    gps = f"Latitude={lat} and Longitude={lng}"
                    
                    # Create CAN message with GPS data
                    tag = 0x123  # Arbitrary ID for the GPS message
                    data = bytearray(f"{gps}".encode())
                    
                    # Yield CAN message asynchronously
                    yield can.Message(arbitration_id=tag, data=data)
                except pynmea2.nmea.ChecksumError as e:
                    print(f"Checksum error: {e}")
                except Exception as e:
                    print(f"Error parsing GPS data: {e}")
    
    def close(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("GPS connection closed.")

    # def open_connection(self):
    #     """Explicitly open the GPS serial connection (if needed)."""
    #     try:
    #         if not self.ser or not self.ser.is_open:
    #             self.ser = serial.Serial(self.port, baudrate=self.baud_rate, timeout=self.timeout)
    #             print(f"Successfully connected to GPS on {self.port}")
    #     except serial.SerialException as e:
    #         print(f"Error opening GPS device on {self.port}: {e}")

Interface = CanusbInterface | PicanInterface | TextFileInterface | GPSInterface

# made this it's own function because how you store the mock data could change
def parse_text_file_line(line):
    line = line.replace("\'", "\"")
    raw = json.loads(line)
    tag = raw["id"]
    data = bytearray.fromhex(raw["data"])

    return tag, data

def get_packets(interface: Interface) -> Generator[can.Message, None, None]:
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
            with can.interface.Bus(channel=channel, bustype=bustype) as bus: # type: ignore
                for msg in bus:
                    tag = msg.arbitration_id
                    data = msg.data
                    yield can.Message(arbitration_id=tag, data=data)
        
        case TextFileInterface(file):
            with file.open("r") as receiver:
                bus = receiver.readlines()
                for msg in bus:
                    (tag, data) = parse_text_file_line(msg)
                    sleep(.1)
                    yield can.Message(arbitration_id=tag, data=data)
                    
        case GPSInterface(port, baud_rate):
                gps_interface = GPSInterface(port, baud_rate)  # Initialize GPSInterface
                while True:
                    for gps_data in gps_interface.get_packets():  # Use the GPSInterface's get_packets method
                        yield gps_data  # Yield GPS data as CAN message
                    sleep(1)  # Adjust sleep duration if necessary
         
def can_worker(interface: Interface):
    """
    Worker that processes CAN data.
    It reads the data and updates the corresponding rows.
    """
    for msg in get_packets(interface):
        assert msg is not None

        row = find(rows, lambda r: r.owns(msg, db))
        if row is not None:
            decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
            with row_lock:
                for k, v in decoded.items():
                    row.signals[k].update(v)
                    if k in src.gui.displayables.keys():
                        src.gui.displayables[k] = cast(float, v)
        else:
            print("??? CAN message not processed:", msg)

def gps_worker(gps_interface: GPSInterface):
    """
    Worker that processes GPS data and updates corresponding rows.
    """
    try:
        for msg in gps_interface.get_packets():  # Get CAN messages from GPSInterface
            assert msg is not None

            # Find the row corresponding to this GPS message
            row = find(rows, lambda r: r.owns(msg, db))
            if row is not None:
                try:
                    # Decode the GPS data (CAN message format)
                    decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
                    with row_lock:
                        for k, v in decoded.items():
                            row.signals[k].update(v)
                            if k in src.gui.displayables.keys():
                                src.gui.displayables[k] = cast(float, v)
                except Exception as decode_error:
                    print(f"Error decoding GPS message: {msg}, error: {decode_error}")
            else:
                print("??? GPS message not processed:", msg)
    except Exception as e:
        print(f"Error in gps_worker: {e}")
    finally:
        gps_interface.close()

def start_can_worker():
    """
    Start the can_worker in a separate thread to process CAN data.
    """
    can_interface = PicanInterface()  # Specify your CAN interface type
    can_thread = Thread(target=can_worker, args=(can_interface,), daemon=True)
    can_thread.start()

def start_gps_worker():
    """
    Start the gps_worker in a separate thread to process GPS data.
    """
    gps_interface = GPSInterface(port="/dev/ttyUSB0")  # Specify your GPS device port
    loop = asyncio.new_event_loop()  # Create a new event loop for the worker thread
    asyncio.set_event_loop(loop)  # Set it as the current event loop

    # Start the gps_worker asynchronously in the event loop
    loop.create_task(gps_worker(gps_interface))

    # Run the event loop for this thread
    loop.run_forever()


def start_xbee():
    global xbee, remote
    xbee = XBeeDevice(XBEE_PORT, XBEE_BAUD_RATE)
    xbee.open()

    remote = xbee.get_network().discover_device(REMOTE_NODE_ID)
    assert remote is not None

# Displays the car gui, receives can data, stores it, and sends it over the xbees

if __name__ == "__main__":
    # Start the workers
    start_can_worker()  # Start CAN data worker
    start_gps_worker()  # Start GPS data worker

    # Start XBee communication if necessary
    start_xbee()

    # Create a thread for sending data
    sender = Thread(target=sender_worker, daemon=True)

    # Start the threads
    sender.start()

    # Display
    if args.display:
        root = src.gui.CarDisplay()
        root.mainloop()

    # Keep the program running
    while True:
        input()