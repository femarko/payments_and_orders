from enum import StrEnum
from typing import Optional



class ErrorCode(StrEnum):
    NOT_FOUND = "not found"
    INVALID_DATA = "invalid input data"
    FORBIDDEN_OPERATION = "forbidden operation"
    EXTERNAL_API_ERROR = "external_api_error"


class DomainError(Exception):
    """Base class for domain errors."""
    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class IncompatibleCurrencyError(DomainError):
    def __init__(self, from_currency: str, to_currency: str) -> None:
        self.from_currency = from_currency
        self.to_currency = to_currency
        super().__init__(
            code=ErrorCode.FORBIDDEN_OPERATION,
            message=f"Incompatible currencies: {from_currency} and {to_currency}"
        )


class PaymentError(DomainError): ...


class OrderError(DomainError): ...


class BaseIdError(DomainError): ...


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(code=ErrorCode.NOT_FOUND, message=message)


class BankError(DomainError): ...


class DomainAttributeError(DomainError):
    def __init__(
            self,
            message: str = f"Direct modification of this attribute "
            f"is forbidden. Use domain methods instead.",
            domain_methods: str = ""
        ) -> None:
        final_message = message
        if domain_methods:
            final_message += f"Domain methods: {domain_methods}."
        super().__init__(ErrorCode.FORBIDDEN_OPERATION, final_message)
