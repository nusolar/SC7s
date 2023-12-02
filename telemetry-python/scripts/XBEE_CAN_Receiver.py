from typing import cast
import sqlite3
from pathlib import Path

import cantools.database
from cantools.database.can.database import Database
from digi.xbee.devices import XBeeDevice
from digi.xbee.models.message import XBeeMessage

from src import ROOT_DIR, BUFFERED_XBEE_MSG_END
from src.can.row import Row
from src.util import add_dbc_file
# import src.sql

import src.can_db as can_db

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms_altered.dbc"))

# The port and baud rate of the connected XBee.
#
# The port looks different based on what OS is used (e.g something like  
# "/dev/tty.usbserial-A21SPQED" for MacOS, "COM5" for Windows, # "/dev/ttyUSB0 for Linux").
# The baud rate should be noted on the XBee device itself.
#
# TODO: Generalize this so it's not hard-coded.
PORT = "COM8"
BAUD_RATE = 57600

# Setup the XBee.
#
# TODO: This has a tendency to hang when the script is run twice (the XBee has to be
# unplugged an re-plugged). Fix that.
xbee = XBeeDevice(PORT, BAUD_RATE)
xbee.open()

store_data = True

# Connect to a SQLite database.
if store_data:
    conn = can_db.connect("can_receiving_db")

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

received: list[str] = [] # for buffering
def process_message(message: XBeeMessage) -> None:
    """
    Processes message received over XBee, deserializing it's contents
    and storing it in the base station database.
    """

    # TODO: Buffering sucks. Get rid of the need for this (with more space-efficient serialization).
    s: str = message.data.decode()
    print(s)
    print("\n")
    if s.endswith(BUFFERED_XBEE_MSG_END):
        s = "".join(received) + s[:len(s) - len(BUFFERED_XBEE_MSG_END)]
        received.clear()

        try:
            r = Row.deserialize(s)
        except:
            raise Exception("Error deserializing row")

        if store_data:
            can_db.add_row(conn, r)
    else:
        received.append(s)


if __name__ == "__main__":
    # This script receives CAN data sent by XBee (through sender.py or virtual_sender.py)
    # and stores it in an SQL database.

    # Create a table for each device on the car's CAN network.
    if store_data:
        for row in rows:
            can_db.create_tables(conn, row.name, row.signals.items())
        print("ready to receive")

    # Register the XBee callback
    xbee.add_data_received_callback(process_message)

    # Spin forever
    while True: ...
