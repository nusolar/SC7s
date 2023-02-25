from typing import cast
import sqlite3
from pathlib import Path

import cantools.database
from cantools.database.can.database import Database
from digi.xbee.devices import XBeeDevice
from digi.xbee.models.message import XBeeMessage

from definitions import PROJECT_ROOT, BUFFERED_XBEE_MSG_END
from src.can.row import Row
from src.can.util import add_dbc_file
import can_db

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(PROJECT_ROOT).joinpath("src", "resources", "mppt.dbc")))
add_dbc_file(db, Path(PROJECT_ROOT).joinpath("src", "resources", "motor_controller.dbc"))

# Check PORT command: ls /dev/tty.usb*
PORT = "/dev/tty.usbserial-A21SPQED"
BAUD_RATE = 57600

xbee = XBeeDevice(PORT, BAUD_RATE)
xbee.open()

# Connection
conn = can_db.connect()

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

received = []

def process_message(message: XBeeMessage) -> None:
    s: str = message.data.decode()
    print(s)
    print("\n")
    if s.endswith(BUFFERED_XBEE_MSG_END):
        s = "".join(received) + s[:len(s) - len(BUFFERED_XBEE_MSG_END)]
        received.clear()
        r = Row.deserialize(s)
        can_db.add_row(conn, r.timestamp, r.signals.values(), r.name)
    else:
        received.append(s)

if __name__ == "__main__":
    # Use the main thread to deserialize rows and update the databse
    # as if it were running on the base station

    for row in rows:
        can_db.create_tables(conn, row.name, row.signals.items())
    print("ready to receive")

    xbee.add_data_received_callback(process_message)

    input()
    
