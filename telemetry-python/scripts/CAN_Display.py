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

from src import ROOT_DIR, BUFFERED_XBEE_MSG_END
from src.can.row import Row
from src.util import add_dbc_file, find, unwrap

import src.car_gui as car_display

VIRTUAL_BUS_NAME = "virtbus"

PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600
REMOTE_NODE_ID = "Node"

xbee = XBeeDevice(PORT, BAUD_RATE)
xbee.open()

remote = xbee.get_network().discover_device(REMOTE_NODE_ID)
assert remote is not None

# Thread communication globals
row_lock = Lock()

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms.dbc"))

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
                if k in car_display.displayables.keys():
                    car_display.displayables[k] = v

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
            for chunk in buffered_payload(row.serialize()):
                print(chunk)
                print("\n")
                xbee.send_data(remote, chunk)

#displays the car gui, receives can data, stores it, and sends it over the xbees
if __name__ == "__main__":
    # Start the bus
    # Create a thread to read of the bus and maintain the rows
    accumulator = Thread(target=row_accumulator_worker,
                         args=(can.ThreadSafeBus(channel='can0', bustype='socketcan'),),
                         daemon=True)

    # Create a thread to serialize rows as would be necessary with XBees
    sender = Thread(target=sender_worker, daemon=True)

    #display
    root = car_display.CarDisplay()
    root.mainloop()

    # Start the threads
    accumulator.start()
    sender.start()

    # Spin forever.
    while True: ...
