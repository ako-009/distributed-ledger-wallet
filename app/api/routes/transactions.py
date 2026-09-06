from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.transaction import TransferRequest, TransactionResponse
from app.services.transaction_service import (
    transfer, InsufficientFundsError, WalletNotFoundError
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/transfer", response_model=TransactionResponse, status_code=201)
async def make_transfer(
    transfer_data: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Transfer money between wallets.
    This is an atomic ACID transaction with SELECT FOR UPDATE locking.
    """
    try:
        transaction = await transfer(
            sender_wallet_id=transfer_data.sender_wallet_id,
            receiver_wallet_id=transfer_data.receiver_wallet_id,
            amount=transfer_data.amount,
            db=db,
        )
        return TransactionResponse(
            id=str(transaction.id),
            sender_wallet_id=str(transaction.sender_wallet_id),
            receiver_wallet_id=str(transaction.receiver_wallet_id),
            amount=transaction.amount,
            status=transaction.status
        )
    except InsufficientFundsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except WalletNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )