from typing import cast
from pathlib import Path
import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType
from src.util import add_dbc_file
import time

from src import ROOT_DIR

save_filename = "testInputRaw.txt"
should_save_file = True
save_file = None

def parse_message(msg):
    # print(msg)
    # print({**{"id": msg.arbitration_id}, **cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))})
    datam = {"id": msg.arbitration_id, "data": msg.data.hex(), "timestamp": time.time()}
    print(datam)
    return datam

if __name__ == "__main__":
    # This script reads off a CAN Bus and prints decoded messages.

    # Load in the CAN database file(s) for the nodes on the CAN network.
    db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
    add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))
    # add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms_altered.dbc"))

    with can.Bus(channel='can0', bustype='socketcan') as bus:
        if should_save_file:
            with open(save_filename, 'w') as f:
                while True:
                    # Wait for a message, decode it, and print.
                    msg = bus.recv()
                    f.write(str(parse_message(msg))+"\n")
        else:
            while True:
                # Wait for a message, decode it, and print.
                msg = bus.recv()
                parse_message(msg)
                