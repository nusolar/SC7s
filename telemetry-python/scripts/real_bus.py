from typing import cast
from pathlib import Path

import can
import cantools.database
from cantools.database.can.database import Database
from cantools.typechecking import SignalDictType

from definitions import PROJECT_ROOT

if __name__ == "__main__":
    # Load in the CAN database file(s)
    db = cast(Database, cantools.database.load_file(Path(PROJECT_ROOT).joinpath("src", "resources", "mppt.dbc")))

    with can.ThreadSafeBus(channel='can0', bustype='socketcan') as bus:
        while True:
            msg = bus.recv()
            print({**{"id": msg.arbitration_id},
                   **cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))})

