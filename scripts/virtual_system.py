from typing import cast
from time import sleep
from threading import Thread, Lock
from queue import Queue # threadsafe mpmc queue used to emulate data transfer over XBee
from copy import deepcopy

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType

from src import ROOT_DIR
from src.can.row import Row
from src.util import add_dbc_file, find, unwrap
from src.can.virtual import start_virtual_can_bus
import src.sql
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session
import argparse

import src.gui

VIRTUAL_BUS_NAME = "virtbus"

# Thread communication globals

# Queueused to safely transfer data (in the form of bytes) between threads in the system, 
# enabling the sender and receiver threads to communicate asynchronously.
row_lock = Lock()
# lock to ensure one thread access data at a time
queue: Queue[bytes] = Queue()
 
# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(ROOT_DIR.joinpath("resources", "mppt.dbc")))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "driver_controls.dbc"))

# Initiate command line parser and args "-o,", "--onboard-db" -- with default args 
# Creates path to SQL file and converts path so string format to read SQLite db url
parser = argparse.ArgumentParser()
parser.add_argument(
    "-o",
    "--onboard-db-url",
    type=str,
    default=str(
        URL.create(drivername="sqlite",database=str(ROOT_DIR.joinpath("resources", "virtual_onboard.db")))
    )
)

# -o (onboard-db-url): This argument specifies the URL for the onboard database,
# which is used to store data collected onboard the vehicle.

# -r (remote-db-url): This argument specifies the URL for the remote database, 
# which is used to store data received at the base station after it has been transmitted from the vehicle.

# Adds an argument for the remote database URL, with a default path to "virtual_remote.db".
# If not provided, it defaults to an SQLite database located in the "resources" directory.
parser.add_argument(
    "-r",
    "--remote-db-url",
    type=str,
    default=str(
        URL.create(drivername="sqlite",database=str(ROOT_DIR.joinpath("resources", "virtual_remote.db")))
    )
)

# This line parses the command-line arguments provided by the user.
# The parser object (created earlier) looks for the arguments -o (onboard-db-url) and -r (remote-db-url),
# or it uses the default values if they are not provided.
# The result is stored in args, which is an object containing the parsed arguments.

# For example:

# If the user runs the program like this: python script.py -o "path/to/onboard.db" -r "path/to/remote.db", the args object will contain:
# args.onboard_db_url = "path/to/onboard.db"
# args.remote_db_url = "path/to/remote.db"
args = parser.parse_args()

# onboard_engine is a SQLAlchemy engine object that allows the program to interact with the onboard database 
# (e.g., running queries, creating tables, etc.).
onboard_engine = create_engine(args.onboard_db_url)

# Session(): This creates a session object for interacting with the database through the onboard_engine.
onboard_session = Session(onboard_engine)


remote_engine = create_engine(args.remote_db_url)
remote_session = Session(remote_engine)

# The rows that will be added to the database
# Creates a list of Row objects, one for each CAN bus node, to store and process their data.
rows = [Row(db, node.name) for node in db.nodes]


# Continuously listens for CAN messages on the bus, finds the corresponding Row for the message,
# decodes the message into signal values, updates the relevant Row's signals, and updates the GUI display with new values.
def row_accumulator_worker(bus: can.ThreadSafeBus):
    """
    Observes messages sent on the `bus` and accumulates them in a global row.
    """
    while True:
        msg = bus.recv()
        assert msg is not None
        
        row = find(rows, lambda r: r.owns(msg, db))
        row = unwrap(row)

        decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
        with row_lock:
            for k, v in decoded.items():

                v = cast(float, v)

                row.signals[k].update(v)

                #working with GUI
                if k in src.gui.displayables.keys():
                    src.gui.displayables[k] = v

# The row_accumulator_worker (above) collects and updates CAN message data in real time, 
# while the sender_worker periodically serializes and sends the accumulated data to a queue 
# for transmission or storage.
 
def sender_worker():
    """
    Serializes rows into the queue.
    """
    # Create database tables for each row (CAN node) using the onboard session,
    # initializing them with the row's name and its signal data.
    for row in rows:
        src.sql.create_tables(onboard_session, row.name, row.signals.items())

    while True:
        # Sleep for 2 seconds between each cycle to simulate periodic sending of data.
        sleep(2.0)
        
        # Lock the row data to safely copy it for processing (prevent conflicts with other threads).
        with row_lock:
            copied = deepcopy(rows)
        
        # For each copied row, stamp it with a timestamp, add the row to the onboard database,
        # and serialize it (convert to bytes) before putting it into the queue for transfer.
        for row in copied:
            row.stamp()
            src.sql.add_row(onboard_session, row)  # Add the row to the database
            queue.put(row.serialize())  # Place the serialized row into the queue for sending

# The function below continuously retrieves serialized Row objects from the queue, 
# deserializes them into usable data, and adds the data to the remote database for storage.
def reciever_worker():
    while True:
        r = Row.deserialize(queue.get(), db)
        src.sql.add_row(remote_session, r)


if __name__ == "__main__":
    # This program simulates CAN bus traffic, onboard CAN frame parsing, and XBee data
    # transfer via multiple threads.
    #
    # Virtual CAN bus traffic is simulated by sending random data (which is loosely based
    # on previously collected real data) on a virtual bus. Each node on the CAN bus
    # (e.g. an MPPT at base address 0x600, an MPPT at 0x610, a BMS, ...) is given its
    # own thread to send messages on the bus. These are the device threads.
    #
    # This traffic is monitored and parsed in the accumulator thread,
    # which maintains a row to be sent periodically to the base station for each
    # device. This thread also averages values where appropritate.
    #
    # A sender thread is responsible for periodically reading from these
    # assembled rows, timestamping them, and serializing them into a queue that
    # will be read by the mock receiver thread (the main thread).
    #
    # Upon reception, the main thread deserializes the row and inserts it into a
    # database table.
    
    # Start the virtual bus
    start_virtual_can_bus(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype="virtual"), db)

    # Create a thread to read off the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype='virtual'),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    receiver = Thread(target=reciever_worker, daemon=True)

    accumulator.start()
    sender.start()
    receiver.start()

    # Use the main thread to deserialize rows and update the databse
    # as if it were running on the base station
    for row in rows:
        src.sql.create_tables(remote_session, row.name, row.signals.items())

    root = src.gui.CarDisplay()

    root.mainloop()
