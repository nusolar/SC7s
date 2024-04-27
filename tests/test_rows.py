from src.can.row import CanValue

def test_fetch_without_averaging():
    can_value = CanValue(value=42, is_averaged=False)
    assert can_value.fetch() == 42
    assert can_value.n == 1

def test_fetch_with_averaging():
    can_value = CanValue(value=10, is_averaged=True)
    can_value.update(20)
    can_value.update(30)
    assert can_value.n == 3
    assert can_value.fetch() == 20.0
    assert can_value.n == 0
    assert can_value.value is None

def test_update_without_averaging():
    can_value = CanValue(value=None, is_averaged=False)
    assert can_value.n == 0
    can_value.update(5)
    assert can_value.value == 5

def test_update_with_averaging():
    can_value = CanValue(is_averaged=True)
    assert can_value.n == 0
    can_value.update(10)
    can_value.update(20)
    assert can_value.n == 2
    assert can_value.value == 15.0

def test_update_with_initial_value():
    can_value = CanValue(value=5, is_averaged=True)
    can_value.update(10)
    assert can_value.value == 7.5

def test_fetch_after_update():
    can_value = CanValue(value=5, is_averaged=True)
    can_value.update(10)
    assert can_value.fetch() == 7.5

def test_fetch_reset_after_update():
    can_value = CanValue(value=5, is_averaged=True)
    can_value.update(10)
    can_value.fetch()
    assert can_value.value is None
    assert can_value.n == 0
