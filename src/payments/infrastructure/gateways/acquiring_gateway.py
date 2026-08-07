import time
from typing import Any
import requests
from requests.exceptions import RequestException
from uuid import UUID

from payments.domain.entities.payment import Payment
from payments.domain.errors import (
    BankError,
    ErrorCode,
)
from payments.application.interfaces.bank_gateway_interface import CheckBankStatusResult



class BankGateway:
    def __init__(
            self,
            api_key: str,
            base_url: str
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        
    def _get_with_retry(self, payment_id: UUID) -> dict[str, Any]:
        last_exception = None
        url = self.base_url + "/" + str(payment_id) + "/status"
        for attempt in range(3):
            try:
                response = requests.get(
                    url=url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5
                )
                response.raise_for_status()
                try:
                    result = response.json()
                except ValueError as e:
                    raise BankError(
                        code = ErrorCode.INVALID_RESPONSE,
                        message=f"Invalid JSON from bank"
                    ) from e
                return result
            except RequestException as e:
                last_exception = e
                time.sleep(0.5 * (attempt + 1))
        raise BankError(
            code = ErrorCode.EXTERNAL_API_UNAVAILABLE,
            message=f"Failed to make request to {payment_id}"
        ) from last_exception
    
    def _parse_response(self, bank_response: dict) -> CheckBankStatusResult:
        try:
            status = bank_response["status"]
        except KeyError as e:
            raise BankError(
                code = ErrorCode.INVALID_RESPONSE,
                message=f"No bank status in response: {bank_response}"
            ) from e
        return CheckBankStatusResult(
            status=status,
            error=bank_response.get("error")
        )

    def check_payment(self, payment: Payment) -> CheckBankStatusResult:
        bank_response = self._get_with_retry(
            payment_id=payment.id.value,
        )
        return self._parse_response(bank_response)
