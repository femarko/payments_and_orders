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
    "operation",
    [
        operator.add,
        operator.sub,
        operator.lt,
        operator.gt,
        operator.le,
        operator.ge,
    ],
)
def test_arithmetics_and_ordering_do_not_mutate_operands(operation):
    m1 = Money(Decimal("100"), Currency.RUB)
    m2 = Money(Decimal("50"), Currency.RUB)
    operation(m1, m2)
    assert m1 == Money(Decimal("100"), Currency.RUB)
    assert m2 == Money(Decimal("50"), Currency.RUB)


@pytest.mark.parametrize(
    "operation, a, b, expected",
    [
        (operator.lt, "50", "100", True),
        (operator.lt, "100", "50", False),
        (operator.gt, "100", "50", True),
        (operator.gt, "50", "100", False),
        (operator.le, "50", "100", True),
        (operator.le, "50", "50", True),
        (operator.le, "100", "50", False),
        (operator.ge, "100", "50", True),
        (operator.ge, "50", "50", True),
        (operator.ge, "50", "100", False),
    ],
)
def test_money_ordering_operations(operation, a, b, expected):
    m1 = Money(Decimal(a), Currency.RUB)
    m2 = Money(Decimal(b), Currency.RUB)
    result = operation(m1, m2)
    assert result is expected


@pytest.mark.parametrize(
    "operation",
    [
        operator.lt,
        operator.gt,
        operator.le,
        operator.ge,
    ],
)
def test_money_ordering_operations_different_currency_raises_error(operation):
    rub = Money("100", Currency.RUB)
    usd = Money("100", Currency.USD)
    with pytest.raises(IncompatibleCurrencyError):
        operation(rub, usd)


@pytest.mark.parametrize(
        "other, expected",
        [
            (42, False),
            ("forty_two", False),
            (False, False),
            (42.12323453456, False),
        ]
)
def test_money_comparison_different_types_returns_false(other, expected):
    money = Money(Decimal("100"), Currency.RUB)
    assert (money == other) is expected
    assert (other == money) is expected


@pytest.mark.parametrize(
        "a, b, expected",
        [
            ("50", "50", True),
            ("50", "100", False)
        ]
)
def test_money_comparison_money(a,b, expected):
    m1 = Money(Decimal(a), Currency.RUB)
    m2 = Money(Decimal(b), Currency.RUB)
    assert (m1 == m2) is expected
    assert (m2 == m1) is expected


def test_add_same_currency_returns_sum():
    m1 = Money(amount=Decimal("100"), currency=Currency.RUB)
    m2 = Money(amount=Decimal("100"), currency=Currency.RUB)
    result = m1 + m2
    assert result == Money(Decimal("200"), Currency.RUB)


def test_add_different_currency_raises_error():
    rub = Money(amount=Decimal("100"), currency=Currency.RUB)
    usd = Money(amount=Decimal("100"), currency=Currency.USD)
    with pytest.raises(IncompatibleCurrencyError):
        rub + usd


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


@pytest.mark.parametrize(
        "operation",
        [
            operator.add,
            operator.sub,
            operator.lt,
            operator.gt,
            operator.le,
            operator.ge,
        ]
)
def test_arithmetics_and_ordering_with_non_money_returns_not_supported(operation):
    money = Money(Decimal("100"), Currency.RUB)
    non_money = 42
    with pytest.raises(TypeError):
        operation(money, non_money)


def test_zero_returns_expected_result():
    result = Money.zero()
    assert result == Money(Decimal("0"), Currency.RUB)


@pytest.mark.parametrize(
        "amount, expected",
        [
            ("0", False),
            ("42", True),
            ("-42", True)
        ]
)
def test_money_bool_behavior(amount, expected):
    m = Money(Decimal(amount), Currency.RUB)
    assert bool(m) is expected


def test_zero_is_falsy():
    assert not Money.zero()
