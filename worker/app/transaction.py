import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Literal


class Transaction(BaseModel):
    transaction_id: str
    account_id: str
    transaction_type: Literal["deposit", "withdrawal", "payment"]
    amount: Decimal
    details: str
    timestamp: datetime.datetime

    @classmethod
    def from_dict(cls, data: dict):
        try:
            return cls(
                transaction_id=data['transaction_id'],
                account_id=data['account_id'],
                transaction_type=data['transaction_type'],
                amount=Decimal(str(data['amount'])),
                details=data['details'],
                timestamp=datetime.datetime.fromisoformat(data['timestamp']) 
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid data: {e}")

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "transaction_type": self.transaction_type,
            "amount": str(self.amount),
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

