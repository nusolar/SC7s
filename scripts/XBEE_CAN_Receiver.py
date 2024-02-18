from typing import cast
import argparse

import cantools.database
from cantools.database.can.database import Database
from digi.xbee.devices import XBeeDevice
from digi.xbee.models.message import XBeeMessage
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session

from src import ROOT_DIR, BUFFERED_XBEE_MSG_END
from src.can.row import Row
from src.util import add_dbc_file
import src.can_db as can_db

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(ROOT_DIR.joinpath("resources", "mppt.dbc")))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "bms_altered.dbc"))

parser = argparse.ArgumentParser()

parser.add_argument("--store", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument(
    "--db-url",
    type=str,
    default=str(
        URL.create(drivername="sqlite",database=str(ROOT_DIR.joinpath("resources", "can_receiving.db")))
    )
)
parser.add_argument("--xbee-port", type=str)
parser.add_argument("--xbee-baud-rate", type=int)

args = parser.parse_args()

# Setup the XBee.
#
# TODO: This has a tendency to hang when the script is run twice (the XBee has to be
# unplugged an re-plugged). Fix that.
xbee = XBeeDevice(args.xbee_port, args.xbee_baud_rate)
xbee.open()

# Connect to the database.
session = Session(create_engine(args.db_url)) if args.store else None

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
            r = Row.deserialize(s, db)
        except:
            raise Exception("Error deserializing row")

        if session is not None:
            can_db.add_row(session, r)
    else:
        received.append(s)


if __name__ == "__main__":
    # This script receives CAN data sent by XBee (through sender.py or virtual_sender.py)
    # and stores it in an SQL database.

    # Create a table for each device on the car's CAN network.
    if session is not None:
        for row in rows:
            can_db.create_tables(session, row.name, row.signals.items())
        print("====================Ready to recieve====================")

    # Register the XBee callback
    xbee.add_data_received_callback(process_message)

    # Spin forever
    while True: ...
