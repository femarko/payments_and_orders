from fastapi import (
    APIRouter,
    Depends,
)

from payments.application.dto import (
    PaymentParams,
    MessageResponse,
)
from payments.entrypoints.http.dependencies import (
    get_deposit_payment_uc,
    get_refund_payment_uc,
)
from payments.entrypoints.http.schemas import (
    DepositPaymentRequest,
)



router = APIRouter()


@router.post("/payments/deposit")
async def deposit_payment(
    payload: DepositPaymentRequest,
    uc = Depends(get_deposit_payment_uc)
) -> MessageResponse:
    payment_params = PaymentParams(
        id=payload.payment_id,
        order_id=payload.order_id,
        payment_type=payload.payment_type,
        amount=payload.amount,
        currency=payload.currency
    )
    return uc.execute(payment_params)


@router.post("/payments/{payment_id}/refund")
async def refund_payment(
    payment_id: str,
    uc = Depends(get_refund_payment_uc)
) -> MessageResponse:
    return uc.execute(payment_id)
