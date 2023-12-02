from typing import cast
from time import sleep
from threading import Thread, Lock
from queue import Queue # threadsafe mpmc queue used to emulate data transfer over XBee
from pathlib import Path
from copy import deepcopy

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType

from src import ROOT_DIR
from src.can.row import Row
from src.util import add_dbc_file, find, unwrap
from src.can.virtual import start_virtual_can_bus
# import src.sql
import src.can_db as can_db
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session

import src.car_gui as car_display

VIRTUAL_BUS_NAME = "virtbus"

# Thread communication globals
row_lock = Lock()
queue: Queue[str] = Queue()
 
# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))
# add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms_altered.dbc"))

onboard_engine = create_engine(
    URL.create(drivername="sqlite",database=str(Path(ROOT_DIR).joinpath("resources", "virtual_onboard.db")))
)
onboard_session = Session(onboard_engine)

remote_engine = create_engine(
    URL.create(drivername="sqlite",database=str(Path(ROOT_DIR).joinpath("resources", "virtual_remote.db")))
)
remote_session = Session(remote_engine)



# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

def row_accumulator_worker(bus: can.ThreadSafeBus):
    global car_display
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
                if k in car_display.displayables.keys():
                    car_display.displayables[k] = v
                    
def sender_worker():
    """
    Serializes rows into the queue.
    """
    for row in rows:
        can_db.create_tables(onboard_session, row.name, row.signals.items())

    while True:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            row.stamp()
            can_db.add_row(onboard_session, row)
            queue.put(row.serialize())

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

    # Create a thread to read of the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype='virtual'),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    accumulator.start()
    sender.start()

    # Use the main thread to deserialize rows and update the databse
    # as if it were running on the base station
    for row in rows:
        can_db.create_tables(remote_session, row.name, row.signals.items())

    while True:
        r = Row.deserialize(queue.get())
        can_db.add_row(remote_session, r)
