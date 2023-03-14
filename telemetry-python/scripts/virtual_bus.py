from typing import cast, Optional
from time import sleep
from threading import Thread, Lock
from queue import Queue # threadsafe mpmc queue used to emulate data transfer over XBee
import sqlite3
from pathlib import Path
from copy import deepcopy

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from fastapi import FastAPI

from src import ROOT_DIR
from src.can.row import Row
from src.can.stats import mock_value
from src.util import add_dbc_file
import src.sql

VIRTUAL_BUS_NAME = "virtbus"

# Thread communication globals
row_lock = Lock()
queue: Queue[str] = Queue()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

# Spin up API
app = FastAPI()

def device_worker(bus: can.ThreadSafeBus, my_messages:  list[cantools.database.Message]) -> None:
    """
    Constantly sends messages on the `bus`.
    """
    while True:
        for msg in my_messages:
            d = {}
            for sig in msg.signals:
                d[sig.name] = mock_value(msg.senders[0], sig.name)
            data = msg.encode(d)
            bus.send(can.Message(arbitration_id=msg.frame_id, data=data))
            sleep(0.1)
        sleep(1)

def row_accumulator_worker(bus: can.ThreadSafeBus):
    """
    Observes messages sent on the `bus` and accumulates them in a global row.
    """
    while True:
        msg = bus.recv()
        assert msg is not None
        
        i = next(i for i, r in enumerate(rows) if r.owns(msg, db))
        decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
        with row_lock:
            for k, v in decoded.items():
                rows[i].signals[k].update(v)

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
            queue.put(row.serialize())

@app.get("/latest")
async def get_latest(dev_name: str) -> Optional[Row]:
    with row_lock:
        return next((row for row in rows if row.name == dev_name), None)

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

    # Create a thread for each node in the database file. 
    # Each thread gets a copy of the bus for writing.
    # Each thread sends only the messages that the corresponding device would send.
    dev_threads: list[Thread] = []
    for i, node in enumerate(db.nodes):
        dev_threads.append(Thread(target=device_worker,
                                  args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype="virtual"),
                                        [msg for msg in db.messages if msg.senders[0] == db.nodes[i].name]),
                                  daemon=True))

    # Create a thread to read of the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype='virtual'),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    # Start all the threads.
    for thread in dev_threads:
        thread.start()

    accumulator.start()
    sender.start()

    # Use the main thread to deserialize rows and update the databse
    # as if it were running on the base station
    conn   = sqlite3.connect(Path(ROOT_DIR).joinpath("resources", "virt.db"))
    cursor = conn.cursor()

    for row in rows:
        src.sql.create_table(row, cursor)
    conn.commit()

    while True:
        r = Row.deserialize(queue.get())
        src.sql.insert_row(r, cursor)
        conn.commit()
