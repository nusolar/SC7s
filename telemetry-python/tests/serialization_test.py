import unittest
from src import ROOT_DIR
from pathlib import Path
import random
from src.can.row import CanValue, Row
from datetime import datetime

#Testing for Daniel
class TestCANSerialization(unittest.TestCase):
    def setUp(self):
        self.timestamp = datetime.now().timestamp()
        self.sig_folder = Path(ROOT_DIR).joinpath("resources","signal_keys")

    def test_devices(self):
        MPPT_addresses = ["MPPT_0x600", "MPPT_0x610", "MPPT_0x620","BMS","MOTOR_CONTROLLER_0x400","Third_Party_Device"]
        for name in MPPT_addresses:
            with open(self.sig_folder.joinpath(f"{name}_sig_keys.txt"), "r") as sig_file:
                sig_keys = sig_file.read().split(",")
            signals = {}
            for key in sig_keys:
                val = random.uniform(0,15)
                signals[key] = CanValue(val, is_averaged=False)
            row = Row(signals, name, self.timestamp)
            serialized = Row.deserialize(row.serialize())
            self.assertTrue(hasattr(serialized,"name"))
            self.assertTrue(hasattr(serialized,"timestamp"))
            self.assertTrue(hasattr(serialized,"signals"))
            self.assertEqual(row.timestamp, serialized.timestamp)
            self.assertEqual(row.name, serialized.name)
            for key in sig_keys:
                self.assertEqual(row.signals[key].value, serialized.signals[key].value)
            
if __name__ == "__main__":
    unittest.main()
