from enum import StrEnum



class ErrorCode(StrEnum):
    NOT_FOUND = "not found"
    INVALID_DATA = "invalid input data"
    FORBIDDEN_OPERATION = "forbidden operation"


class DomainError(Exception):
    """Base class for domain errors."""
    def __init__(
            self,
            code: ErrorCode,
            message: str,
            *args
    ) -> None:
        super().__init__(code, message, *args)
        self.code = code



class IncompatibleCurrencyError(DomainError):
    def __init__(
            self,
            from_currency: str,
            to_currency: str
        ) -> None:
        super().__init__(
            code= ErrorCode.FORBIDDEN_OPERATION,
            message=f"Incompatible currencies: {from_currency} "
                    f"and {to_currency}"
        )


class PaymentError(DomainError):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(code, message)


class OrderStatusError(DomainError):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(code, message)
