from typing import cast
from pathlib import Path
import unittest
import random
from datetime import datetime
from copy import deepcopy

import cantools.database
from cantools.database.can.database import Database

from src import ROOT_DIR
from src.util import add_dbc_file
from src.can.row import CanValue, Row

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, Path(ROOT_DIR).joinpath("resources", "bms_altered.dbc"))

class TestCANSerialization(unittest.TestCase):
    def setUp(self):
        self.timestamp = datetime.now().timestamp()
        self.sig_folder = ROOT_DIR.joinpath("resources", "signal_keys")

    def test_devices(self):
        """
        Test (de)serialization for all devices sending CAN data on a network.
        """

        device_addresses = [n.name for n in db.nodes]

        for name in device_addresses:
            keys = Row.signal_names(name, db)
            signals = {k: CanValue(random.uniform(0, 15)) for k in keys}

            row = Row(signals, name, self.timestamp)

            # Deepcopy to avoid resetting the row when serializing
            serialized = Row.deserialize(deepcopy(row).serialize(), db)

            self.assertEqual(row.timestamp, serialized.timestamp)
            self.assertEqual(row.name, serialized.name)

            self.assertEqual(
                {k: v.value for (k, v) in row.signals.items()},
                {k: v.value for (k, v) in serialized.signals.items()}
            )
            
if __name__ == "__main__":
    unittest.main()
