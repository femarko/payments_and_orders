import pytest
import operator
from decimal import Decimal

from payments.domain.errors import IncompatibleCurrencyError
from payments.domain.value_objects import Money
from payments.domain.enums import Currency


def test_money_converts_string_to_decimal():
    m = Money("100", Currency.RUB)
    assert m.amount == Decimal("100")


@pytest.mark.parametrize(
    "operation, expected",
    [
        (operator.add, Decimal("150")),
        (operator.sub, Decimal("50")),
    ],
)
def test_operations_do_not_mutate_operands(operation, expected):
    m1 = Money(Decimal("100"), Currency.RUB)
    m2 = Money(Decimal("50"), Currency.RUB)
    result = operation(m1, m2)
    assert m1 == Money(Decimal("100"), Currency.RUB)
    assert m2 == Money(Decimal("50"), Currency.RUB)
    assert result == Money(expected, Currency.RUB)


def test_add_same_currency_returns_sum():
    m1 = Money(amount=Decimal("100"), currency=Currency.RUB)
    m2 = Money(amount=Decimal("100"), currency=Currency.RUB)
    result = m1 + m2
    assert result == Money(Decimal("200"), Currency.RUB)


def test_add_different_currency_raises_error():
    rub = Money(amount=Decimal("100"), currency=Currency.RUB)
    usd = Money(amount=Decimal("100"), currency=Currency.USD)
    with pytest.raises(IncompatibleCurrencyError):
        result = rub + usd


def test_subtract_same_currency_returns_expected_result():
    m1 = Money(Decimal("200"), Currency.RUB)
    m2 = Money(Decimal("100"), Currency.RUB)
    result = m1 - m2
    assert result == Money(Decimal("100"), Currency.RUB)


def test_subtract_different_currency_raises_error():
    rub = Money(Decimal("100"), Currency.RUB)
    usd = Money(Decimal("50"), Currency.USD)
    with pytest.raises(IncompatibleCurrencyError):
        rub - usd


def test_zero_returns_expected_result():
    result = Money.zero()
    assert result == Money(Decimal("0"), Currency.RUB)
