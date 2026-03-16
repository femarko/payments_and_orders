class DomainError(Exception):
    """Base class for domain errors."""


class IncompatibleCurrencyError(DomainError):
    def __init__(self, from_currency: str, to_currency: str) -> None:
        super().__init__(
            f"Incompatible currencies: {from_currency} and {to_currency}"
        )


class PaymentError(DomainError): ...
