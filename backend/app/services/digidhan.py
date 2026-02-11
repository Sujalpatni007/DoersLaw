"""
Digidhan Payment Gateway - Mock Version
Interface for court fee and service payments
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import uuid
import random
import asyncio
import logging

logger = logging.getLogger("DIGIDHAN")


class PaymentStatus(str, Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    COURT_FEE = "court_fee"
    STAMP_DUTY = "stamp_duty"
    REGISTRATION_FEE = "registration_fee"
    LAWYER_FEE = "lawyer_fee"
    SERVICE_FEE = "service_fee"


class PaymentMethod(str, Enum):
    UPI = "upi"
    NETBANKING = "netbanking"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    WALLET = "wallet"


@dataclass
class Payment:
    id: str
    user_id: int
    case_id: Optional[str]
    payment_type: PaymentType
    amount: float
    currency: str
    method: PaymentMethod
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    transaction_id: Optional[str]
    receipt_url: Optional[str]
    metadata: Dict
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "case_id": self.case_id,
            "payment_type": self.payment_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "method": self.method.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "transaction_id": self.transaction_id,
            "receipt_url": self.receipt_url,
            "metadata": self.metadata,
        }


class DigidhanService:
    """
    Mock Payment Gateway Integration
    Simulates payment processing for court fees
    """
    
    def __init__(self):
        self.payments: Dict[str, Payment] = {}
        self.fee_schedule = {
            PaymentType.COURT_FEE: {"base": 500, "per_lakh": 100},
            PaymentType.STAMP_DUTY: {"base": 1000, "per_lakh": 500},
            PaymentType.REGISTRATION_FEE: {"base": 200, "per_transaction": 50},
            PaymentType.LAWYER_FEE: {"consultation": 1000, "per_hearing": 2000},
            PaymentType.SERVICE_FEE: {"platform": 99, "document_processing": 49},
        }
    
    def calculate_fee(
        self,
        payment_type: PaymentType,
        dispute_value: float = 0,
        additional_services: List[str] = None,
    ) -> Dict:
        """Calculate fees based on dispute value"""
        schedule = self.fee_schedule.get(payment_type, {})
        
        base = schedule.get("base", 0)
        per_lakh = schedule.get("per_lakh", 0)
        
        # Calculate based on dispute value
        lakhs = dispute_value / 100000
        variable = lakhs * per_lakh
        
        total = base + variable
        
        # Add GST (18%)
        gst = total * 0.18
        grand_total = total + gst
        
        return {
            "base_fee": base,
            "variable_fee": round(variable, 2),
            "subtotal": round(total, 2),
            "gst": round(gst, 2),
            "grand_total": round(grand_total, 2),
            "breakdown": {
                "base": base,
                "per_lakh_rate": per_lakh,
                "dispute_value_lakhs": round(lakhs, 2),
            }
        }
    
    async def initiate_payment(
        self,
        user_id: int,
        payment_type: PaymentType,
        amount: float,
        method: PaymentMethod,
        case_id: str = None,
        metadata: Dict = None,
    ) -> Payment:
        """Initiate a payment"""
        payment = Payment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            case_id=case_id,
            payment_type=payment_type,
            amount=amount,
            currency="INR",
            method=method,
            status=PaymentStatus.INITIATED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            transaction_id=None,
            receipt_url=None,
            metadata=metadata or {},
        )
        
        self.payments[payment.id] = payment
        
        logger.info(f"💳 Payment initiated: {payment.id} for ₹{amount}")
        
        return payment
    
    async def process_payment(self, payment_id: str) -> Dict:
        """Process/simulate payment (mock)"""
        payment = self.payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found"}
        
        payment.status = PaymentStatus.PROCESSING
        payment.updated_at = datetime.now()
        
        # Simulate payment processing
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # 95% success rate in mock
        success = random.random() < 0.95
        
        if success:
            payment.status = PaymentStatus.SUCCESS
            payment.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
            payment.receipt_url = f"/receipts/{payment.id}.pdf"
            
            logger.info(f"✅ Payment successful: {payment.transaction_id}")
            
            return {
                "success": True,
                "payment_id": payment.id,
                "transaction_id": payment.transaction_id,
                "amount": payment.amount,
                "receipt_url": payment.receipt_url,
            }
        else:
            payment.status = PaymentStatus.FAILED
            
            logger.warning(f"❌ Payment failed: {payment.id}")
            
            return {
                "success": False,
                "payment_id": payment.id,
                "error": "Payment declined by bank",
                "retry_allowed": True,
            }
    
    async def get_payment_status(self, payment_id: str) -> Optional[Dict]:
        """Get payment status"""
        payment = self.payments.get(payment_id)
        if payment:
            return payment.to_dict()
        return None
    
    async def refund_payment(self, payment_id: str, reason: str) -> Dict:
        """Refund a payment (mock)"""
        payment = self.payments.get(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found"}
        
        if payment.status != PaymentStatus.SUCCESS:
            return {"success": False, "error": "Only successful payments can be refunded"}
        
        await asyncio.sleep(0.5)
        
        payment.status = PaymentStatus.REFUNDED
        payment.updated_at = datetime.now()
        payment.metadata["refund_reason"] = reason
        payment.metadata["refund_date"] = datetime.now().isoformat()
        
        logger.info(f"💸 Payment refunded: {payment.id}")
        
        return {
            "success": True,
            "payment_id": payment.id,
            "refund_amount": payment.amount,
            "reason": reason,
        }
    
    def get_user_payments(self, user_id: int) -> List[Dict]:
        """Get all payments for a user"""
        return [
            p.to_dict() for p in self.payments.values()
            if p.user_id == user_id
        ]


# Singleton
_digidhan_service: Optional[DigidhanService] = None

def get_digidhan_service() -> DigidhanService:
    global _digidhan_service
    if _digidhan_service is None:
        _digidhan_service = DigidhanService()
    return _digidhan_service
