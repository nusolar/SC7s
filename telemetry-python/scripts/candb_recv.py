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
import src.can_db as can_db

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms_altered.dbc"))

PORT = "/dev/tty.usbserial-A21SPQED"
BAUD_RATE = 57600

xbee = XBeeDevice(PORT, BAUD_RATE)
xbee.open()

# Connection
conn = can_db.connect("can_receiving_db")

# The rows that will be added to the database
rows = [Row(db, node.name) for node in db.nodes]

received: list[str] = []

def process_message(message: XBeeMessage) -> None:
    s: str = message.data.decode()
    print(s)
    print("\n")
    if s.endswith(BUFFERED_XBEE_MSG_END):
        s = "".join(received) + s[:len(s) - len(BUFFERED_XBEE_MSG_END)]
        received.clear()
        r = Row.deserialize(s)
        can_db.add_row(conn, r)
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
