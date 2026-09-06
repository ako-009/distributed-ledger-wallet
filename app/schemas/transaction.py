from decimal import Decimal
import uuid
from pydantic import BaseModel


class TransferRequest(BaseModel):
    sender_wallet_id: str
    receiver_wallet_id: str
    amount: Decimal


class TransactionResponse(BaseModel):
    id: str
    sender_wallet_id: str
    receiver_wallet_id: str
    amount: Decimal
    status: str

    class Config:
        from_attributes = True