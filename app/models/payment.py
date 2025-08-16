from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from app.models.transaction import MoneyDecimal


class PaymentResponse(BaseModel):
    message: str
    amount: str
    new_balance: str
    transaction_id: Optional[int]
    timestamp: datetime

class BalanceHistoryItem(BaseModel):
    id: Optional[int]
    type: str
    amount: str
    timestamp: str
    transaction_type: str

class BalanceHistoryResponse(BaseModel):
    username: str
    total_balance: str
    history_months: int
    balances: List[BalanceHistoryItem]
    total_transactions: int

class QRCodeResponse(BaseModel):
    qr_id: str
    qr_type: str
    amount: Optional[MoneyDecimal] = None
    expire: Optional[str] = None


class PaymentRequest(BaseModel):
    amount: MoneyDecimal
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": "100.50"
            }
        }
    }

class TransferRequest(PaymentRequest):
    recipient_username: str
    description: str = ""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": "50.00",
                "recipient_username": "john_doe",
                "description": "Payment for lunch"
            }
        }
    }

class QRRequest(PaymentRequest):
    pass

class PaymentCollectionRequest(PaymentRequest):
    max_usercount: int = 5
    expire: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": "100.00",
                "max_usercount": 5,
                "description": "Group payment for dinner"
            }
        }
    }
