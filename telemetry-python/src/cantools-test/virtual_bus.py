from typing import cast
from time import sleep
from threading import Thread, Lock
from queue import Queue # threadsafe mpmc queue used to emulate data transfer over XBee
import sqlite3
from pathlib import Path
from copy import deepcopy

import can
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType, StringPathLike
import cantools.database
from cantools.database.can.formats import dbc

from definitions import PROJECT_ROOT
from rowify import Row
from stats import mock_value

def add_dbc_file(self: Database, filename: StringPathLike, encoding: str = 'cp1252') -> None:
        with open(filename, 'r', encoding=encoding) as fp:
            string = fp.read()
            database = dbc.load_string(string, self._strict, sort_signals=self._sort_signals) # type: ignore

            self._messages += database.messages
            self._nodes += database.nodes
            self._buses = database.buses
            self._version = database.version
            self._dbc = database.dbc
            self.refresh()


VIRTUAL_BUS_NAME = "virtbus"

# Thread communication globals
row_lock = Lock()
queue: Queue[str] = Queue()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(PROJECT_ROOT).joinpath("src", "cantools-test", "mppt.dbc")))
add_dbc_file(db, Path(PROJECT_ROOT).joinpath("src", "cantools-test", "motor_controller.dbc"))

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]


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
    Observes messages sent on the `bus` and accumulates them in a global row
    """
    while True:
        msg = bus.recv()
        assert msg is not None
        
        i = next(i for i, r in enumerate(rows) if r.owns(msg, db))
        decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
        with row_lock:
            for k, v in decoded.items():
                rows[i].signals[cast(str, k)].update(v)

def sender_worker():
    """
    Serializes rows into the queue
    """
    while True:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            row.stamp()
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
    conn   = sqlite3.connect(Path(PROJECT_ROOT).joinpath("src", "cantools-test", "virt.db"))
    cursor = conn.cursor()

    for row in rows:
        row.sql_create_table(cursor)
    conn.commit()

    while True:
        r = Row.deserialize(queue.get())
        r.sql_insert_row(cursor)
        conn.commit()
