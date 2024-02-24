import unittest
from src.can.row import CanValue

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

if __name__ == '__main__':
    unittest.main()
