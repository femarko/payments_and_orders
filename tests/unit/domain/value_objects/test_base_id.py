from uuid import UUID

from payments.domain.value_objects import BaseId


def test_baseid_new_creates_unique_ids():
    id1 = BaseId.new()
    id2 = BaseId.new()
    assert isinstance(id1.value, UUID)
    assert id1 != id2


def test_baseid_str_and_repr():
    b = BaseId.new()
    assert str(b) == str(b.value)
    assert repr(b) == f"BaseId({b.value})"
