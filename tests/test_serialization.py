from typing import cast
import random
from datetime import datetime
from copy import deepcopy

import cantools.database
from cantools.database.can.database import Database

from src import ROOT_DIR
from src.util import add_dbc_file
from src.can.row import CanValue, Row

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(ROOT_DIR.joinpath("resources", "mppt.dbc")))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "bms_altered.dbc"))

def test_devices():
    """
    Test (de)serialization for all devices sending CAN data on a network.
    """
    timestamp = datetime.now().timestamp()

    device_addresses = [n.name for n in db.nodes]

    for name in device_addresses:
        keys = Row.signal_names(name, db)
        signals = {k: CanValue(random.uniform(0, 15)) for k in keys}

        row = Row(signals, name, timestamp)

        # Deepcopy to avoid resetting the row when serializing
        serialized = Row.deserialize(deepcopy(row).serialize(), db)

        assert row.timestamp == serialized.timestamp
        assert row.name == serialized.name

        assert {k: v.value for (k, v) in row.signals.items()} \
                == {k: v.value for (k, v) in serialized.signals.items()}
