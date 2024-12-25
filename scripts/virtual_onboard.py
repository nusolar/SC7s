# TODO: This file repeats a lot of the same code as `onboard.py`.
# Fix that.

from typing import cast
from time import sleep
from threading import Thread, Lock
from copy import deepcopy

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from digi.xbee.devices import XBeeDevice

import sys
import os

# Add the parent directory of `scripts` and `src` to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import ROOT_DIR
from src.can.row import Row
from src.can.virtual import start_virtual_can_bus
from src.util import add_dbc_file

VIRTUAL_BUS_NAME = "virtbus"

XBEE_PORT = "COM9"
XBEE_BAUD_RATE = 9600

REMOTE_NODE_ID = "Node"

xbee = None
remote = None
should_display = False

# Thread communication globals
row_lock = Lock()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(ROOT_DIR.joinpath("resources", "mppt.dbc")))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

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
                row.signals[k].update(v)
                if k in src.gui.displayables.keys():
                    src.gui.displayables[k] = cast(float, v)

def sender_worker():
    """
    Serializes rows into the queue.
    """
    while True:
        sleep(2.0)
        with row_lock:
            copied = deepcopy(rows)
        for row in copied:
            unwrap(xbee).send_data(remote, row.serialize())

def start_xbee():
    global xbee, remote
    xbee = XBeeDevice(XBEE_PORT, XBEE_BAUD_RATE)
    xbee.open()

    remote = xbee.get_network().discover_device(REMOTE_NODE_ID)
    assert remote is not None

if __name__ == "__main__":
    # Establish XBee connection
    start_xbee()

    # Start the virtual bus
    start_virtual_can_bus(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype="virtual"), db)

    # Create a thread to read of the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype="virtual"),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    # Start the threads
    accumulator.start()
    sender.start()

    #display
    if should_display:
        root = src.gui.CarDisplay()
        root.mainloop()

    # Spin forever.
    while True:
        input()
