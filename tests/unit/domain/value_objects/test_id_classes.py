import pytest
from uuid import UUID

from payments.domain.value_objects import BaseId
from payments.domain.errors import BaseIdError



def test_base_id_from_string_method_creates_base_id_object_from_string():
    base_id = BaseId.from_str("123e4567-e89b-12d3-a456-426614174000")
    assert isinstance(base_id, BaseId)
    assert isinstance(base_id.value, UUID)


def test_base_id_from_string_method_raises_error_with_invalid_string():
    invalid_string = "123"
    with pytest.raises(BaseIdError, match=f"Invalid UUID string: `{invalid_string}`"):
        BaseId.from_str(invalid_string)
