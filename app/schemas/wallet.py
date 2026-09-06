from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel


class WalletCreate(BaseModel):
    currency: str = "INR"


class WalletResponse(BaseModel):
    id: str
    user_id: str
    balance: Decimal
    currency: str
    is_active: bool

    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    wallet_id: str
    balance: Decimal
    currency: str