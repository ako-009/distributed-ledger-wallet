import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id"),
        nullable=False
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id"),
        nullable=False
    )
    # "debit" or "credit"
    entry_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    # Snapshot of balance before and after — immutable audit trail
    balance_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="ledger_entries"
    )
    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="ledger_entries"
    )

    def __repr__(self):
        return f"<LedgerEntry {self.entry_type} {self.amount}>"