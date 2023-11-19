import unittest
from src import ROOT_DIR
import random
from src.can.row import CanValue, Row
from datetime import datetime
from copy import deepcopy

class TestCANSerialization(unittest.TestCase):
    def setUp(self):
        self.timestamp = datetime.now().timestamp()
        self.sig_folder = ROOT_DIR.joinpath("resources", "signal_keys")

    def test_devices(self):
        """
        Test (de)serialization for all devices sending CAN data on a network.
        """

        device_addresses = [
            "MPPT_0x600", "MPPT_0x610", "MPPT_0x620", "BMS", "MOTOR_CONTROLLER_0x400", "Third_Party_Device"
        ]

        for name in device_addresses:
            with open(self.sig_folder.joinpath(f"{name}_sig_keys.txt"), "r") as sig_file:
                sig_keys = sig_file.read().split(",")

            signals = {k: CanValue(random.uniform(0, 15)) for k in sig_keys}

            row = Row(signals, name, self.timestamp)

            # Deepcopy to avoid resetting the row when serializing
            serialized = Row.deserialize(deepcopy(row).serialize())

            self.assertEqual(row.timestamp, serialized.timestamp)
            self.assertEqual(row.name, serialized.name)
            for key in sig_keys:
                self.assertEqual(row.signals[key].value, serialized.signals[key].value)
            
if __name__ == "__main__":
    unittest.main()
