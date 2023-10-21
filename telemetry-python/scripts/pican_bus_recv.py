from typing import cast
from pathlib import Path

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from src.util import add_dbc_file

from src import ROOT_DIR

if __name__ == "__main__":
    # This script reads off a CAN Bus and prints decoded messages.

    # Load in the CAN database file(s) for the nodes on the CAN network.
    db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
    add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))
    add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms_altered.dbc"))

    with can.ThreadSafeBus(channel='can0', bustype='socketcan') as bus:
        while True:
            # Wait for a message, decode it, and print.
            msg = bus.recv()
            print({**{"id": msg.arbitration_id},
                   **cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))})

