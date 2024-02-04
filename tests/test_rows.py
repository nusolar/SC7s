import unittest
import sys
sys.path.insert(0, '../src')
from src.can.row import Row, CanValue
import cantools.database
from cantools.database.can.database import Database
from typing import cast
from src import ROOT_DIR

class TestCanValue(unittest.TestCase):
    def test_fetch_without_averaging(self):
        can_value = CanValue(value=42, is_averaged=False)
        self.assertEqual(can_value.fetch(), 42)
        self.assertEqual(can_value.n,1)

    def test_fetch_with_averaging(self):
        can_value = CanValue(value=10, is_averaged=True)
        can_value.update(20)
        can_value.update(30)
        self.assertEqual(can_value.n,3)
        self.assertEqual(can_value.fetch(), 20.0)
        self.assertEqual(can_value.n, 0)
        self.assertEqual(can_value.value, None)

    def test_update_without_averaging(self):
        can_value = CanValue(value=None, is_averaged=False)
        self.assertEqual(can_value.n,0)
        can_value.update(5)
        self.assertEqual(can_value.value, 5)

    def test_update_with_averaging(self):
        can_value = CanValue(is_averaged=True)
        self.assertEqual(can_value.n,0)
        can_value.update(10)
        can_value.update(20)
        self.assertEqual(can_value.n,2)
        self.assertEqual(can_value.value, 15.0)

    def test_update_with_initial_value(self):
        can_value = CanValue(value=5, is_averaged=True)
        can_value.update(10)
        self.assertEqual(can_value.value, 7.5)

    def test_fetch_after_update(self):
        can_value = CanValue(value=5, is_averaged=True)
        can_value.update(10)
        self.assertEqual(can_value.fetch(), 7.5)

    def test_fetch_reset_after_update(self):
        can_value = CanValue(value=5, is_averaged=True)
        can_value.update(10)
        can_value.fetch()
        self.assertIsNone(can_value.value)
        self.assertEqual(can_value.n, 0)
        
class TestRow(unittest.TestCase):
    # def test_init_with_database(self):
    #     database = Mock()
    #     msg = database.messages[0]
    #     row = Row(database, msg.senders[0])
    #     self.assertEqual(row.name, msg.senders[0])
    #     self.assertTrue(all(signal.name in row.signals for signal in msg.signals))

    # def test_init_with_dict(self):
    #     signals = {'signal1': CanValue(), 'signal2': CanValue()}
    #     row = Row(signals, 'test_row')
    #     self.assertEqual(row.name, 'test_row')
    #     self.assertEqual(row.signals, signals)

    # def test_init_unknown_type_raises_exception(self):
    #     with self.assertRaises(Exception):
    #         Row(123, 'test_row')

    # def test_owns_true(self):
    #     msg = Mock()
    #     msg.arbitration_id = 123
    #     msg.senders = ['test_row']
    #     db = cast(Database, cantools.database.load_file(ROOT_DIR.joinpath("resources", "mppt.dbc")))
    #     db.messages = [Mock(frame_id=123, senders=['test_row'])]
    #     row = Row(db, 'test_row')
    #     self.assertTrue(row.owns(msg, db))

    # def test_owns_false(self):
    #     msg = Mock()
    #     msg.arbitration_id = 123
    #     msg.senders = ['other_row']
    #     db = Mock()
    #     db.messages = [Mock(frame_id=123, senders=['test_row'])]
    #     row = Row(db, 'test_row')
    #     self.assertFalse(row.owns(msg, db))

    def test_stamp(self):
        row = Row({}, 'test_row')
        row.stamp()
        self.assertIsNotNone(row.timestamp)

    def test_serialize(self):
        signals = {'signal1': CanValue(10), 'signal2': CanValue(20)}
        row = Row(signals, 'test_row', timestamp=123456789)
        serialized = row.serialize()
        expected = '{"timestamp": 123456789, "name": "test_row", "signals": {"signal1": 10, "signal2": 20}}'
        self.assertEqual(serialized, expected)

    def test_serialize_unstamped_row_raises_exception(self):
        row = Row({}, 'test_row')
        with self.assertRaises(Exception):
            row.serialize()

    def test_deserialize(self):
        serialized = '{"timestamp": 123456789, "name": "test_row", "signals": {"signal1": 10, "signal2": 20}}'
        deserialized = Row.deserialize(serialized)
        self.assertEqual(deserialized.name, 'test_row')
        self.assertEqual(deserialized.timestamp, 123456789)
        self.assertEqual(deserialized.signals['signal1'].fetch(), 10)
        self.assertEqual(deserialized.signals['signal2'].fetch(), 20)

if __name__ == '__main__':
    unittest.main()