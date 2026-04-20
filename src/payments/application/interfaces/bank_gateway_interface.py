from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import (
    Protocol,
    Optional,
)

from payments.domain.entities.payment import Payment
from payments.domain.enums import PaymentStatus



@dataclass
class CheckBankStatusResult:
    status: PaymentStatus
    error: Optional[str]


class BankGatewayProto(Protocol):
    api_key: str
    
    def check_payment(self, payment: Payment) -> CheckBankStatusResult: ...
