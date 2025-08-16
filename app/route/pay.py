from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from fastapi import APIRouter, Depends, Query, Request, Response

from app.utils.database import AsyncSessionDep
from app.exceptions.user import UserNotFoundException
from app.models.qrcode import QRCode, QRType
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.models.payment import PaymentRequest, PaymentResponse, BalanceHistoryResponse, BalanceHistoryItem, QRCodeResponse, QRRequest, TransferRequest, PaymentCollectionRequest
from app.utils.security import get_current_user
from app.exceptions.payment import InvalidAmountException, InsufficientBalanceException, TransactionNotFoundException
from app.utils.qr_gen import create_qr_code
from app.utils.logging_config import logger
from app.utils.config import settings


router = APIRouter(
    prefix="/api/pay",
    tags=["pay"]
)

@router.post("/topup", response_model=PaymentResponse)
async def topup(
    payment: PaymentRequest,
    session: AsyncSessionDep, 
    current_user: User = Depends(get_current_user)
):
    amount = payment.amount
    try:
        # Validate amount
        if amount <= Decimal('0.00'):
            logger.warning(f"Invalid top-up amount: ${amount} for user {current_user.username}")
            raise InvalidAmountException("Top-up amount must be greater than zero")
        
        # Set limits for top-up
        # if amount > Decimal('10000.00'):
        #     logger.warning(f"Top-up amount too large: ${amount} for user {current_user.username}")
        #     raise InvalidAmountException("Top-up amount cannot exceed $10,000")
        
        # Create balance record and transaction tracking
        transaction_record = Transaction(
            user_id=current_user.id,
            amount=amount,
            transaction_type=TransactionType.TOPUP,
            description=f"Top-up of ${amount:.2f}"
        )
        
        session.add(transaction_record)
        
        await session.commit()
        await session.refresh(transaction_record)
        await session.refresh(current_user)
        
        return PaymentResponse(
            message="Top-up processed successfully",
            amount=f"{amount:.2f}",
            new_balance=f"{await current_user.total_balance(session):.2f}",
            transaction_id=transaction_record.id,
            timestamp=transaction_record.timestamp
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Top-up failed for user {current_user.username} | Amount: ${amount} | Error: {type(e).__name__} | Reason: {str(e)}")

@router.post("/withdraw", response_model=PaymentResponse)
async def withdraw(
    payment: PaymentRequest,
    session: AsyncSessionDep, 
    current_user: User = Depends(get_current_user)
):
    amount = payment.amount
    try:
        # Validate amount
        if amount <= Decimal('0.00'):
            raise InvalidAmountException("Withdrawal amount must be greater than zero")

        # Check current balance
        total_balance = await current_user.total_balance(session)
        if total_balance <= Decimal('0.00'):
            raise InsufficientBalanceException("No balance available for withdrawal")

        if amount > total_balance:
            raise InsufficientBalanceException(
                f"Withdrawal amount ${amount:.2f} exceeds available balance ${total_balance:.2f}"
            )

        # # Set reasonable limits for withdrawal
        # if amount > Decimal('5000.00'):
        #     raise InvalidAmountException("Single withdrawal cannot exceed $5,000")
        
        transaction_record = Transaction(
            user_id=current_user.id,
            amount=-amount,
            transaction_type=TransactionType.WITHDRAWAL,
            description=f"Withdrawal of ${amount:.2f}"
        )
        
        session.add(transaction_record)
        
        await session.commit()
        await session.refresh(transaction_record)
        await session.refresh(current_user)
        
        return PaymentResponse(
            message="Withdrawal processed successfully",
            amount=f"{amount:.2f}",
            new_balance=f"{await current_user.total_balance(session):.2f}",
            transaction_id=transaction_record.id,
            timestamp=transaction_record.timestamp
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Withdrawal failed for user {current_user.username} | Amount: ${amount} | Error: {type(e).__name__} | Reason: {str(e)}")
        raise

@router.post("/transfer", response_model=PaymentResponse)
async def transfer(
    payment: TransferRequest,
    session: AsyncSessionDep,
    current_user: User = Depends(get_current_user)
):
    amount = payment.amount
    try:
        recipient_username = payment.recipient_username
        description = payment.description

        if amount <= Decimal('0.00'):
            raise InvalidAmountException("Transfer amount must be greater than zero")
        
        recipient = await User.get_by_username(session, recipient_username)
        if not recipient:
            raise UserNotFoundException(f"User '{recipient_username}' not found")
        
        if recipient.id == current_user.id:
            raise InvalidAmountException("Cannot transfer to yourself")
        
        sender_balance = await current_user.total_balance(session)
        if amount > sender_balance:
            raise InsufficientBalanceException(
                f"Transfer amount ${amount:.2f} exceeds available balance ${sender_balance:.2f}"
            )
        
        sender_transaction = Transaction(
            user_id=current_user.id,
            amount=-amount,
            transaction_type=TransactionType.TRANSFER_SENT,
            description=description or f"Transfer to {recipient_username}",
            reference_user_id=recipient.id
        )
        
        recipient_transaction = Transaction(
            user_id=recipient.id,
            amount=amount,
            transaction_type=TransactionType.TRANSFER_RECEIVED,
            description=description or f"Transfer from {current_user.username}",
            reference_user_id=current_user.id
        )
        
        session.add(sender_transaction)
        session.add(recipient_transaction)
        
        await session.commit()
        await session.refresh(sender_transaction)
        await session.refresh(current_user)
        
        return PaymentResponse(
            message=f"Transfer to {recipient_username} processed successfully",
            amount=f"{amount:.2f}",
            new_balance=f"{await current_user.total_balance(session):.2f}",
            transaction_id=sender_transaction.id,
            timestamp=sender_transaction.timestamp
        )
    except Exception as e:
        logger.error(f"Transfer failed for user {current_user.username} | Amount: ${amount} | Error: {type(e).__name__} | Reason: {str(e)}")
        await session.rollback()
        raise

@router.get("/history", response_model=BalanceHistoryResponse)
async def get_history(
    session: AsyncSessionDep,
    current_user: User = Depends(get_current_user),
    history_months: int = Query(6, ge=1, le=24, description="Number of months of history to retrieve"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
):
    try:
        cutoff_date = datetime.now() - timedelta(days=30 * history_months)
        
        # Get paginated transaction results instead of balance
        offset = (page - 1) * page_size
        filtered_transactions = await User.get_transactions_by_date_paginated(
            session=session,
            user_id=current_user.id,
            from_date=cutoff_date,
            limit=page_size,
            offset=offset
        )
        
        # Count total transactions for pagination info
        total_count = await User.count_transactions_by_date(
            session=session,
            user_id=current_user.id,
            from_date=cutoff_date
        )

        transaction_items = [
            BalanceHistoryItem(
                id=transaction.id,
                type=transaction.transaction_type.value,
                amount=f"{transaction.amount:.2f}",
                timestamp=transaction.timestamp.isoformat(),
                transaction_type=transaction.transaction_type.value
            ) for transaction in filtered_transactions
        ]

        return BalanceHistoryResponse(
            username=current_user.username,
            total_balance=f"{await current_user.total_balance(session):.2f}",
            history_months=history_months,
            balances=transaction_items,
            total_transactions=total_count
        )
    except Exception as e:
        logger.error(f"Get history failed for user {current_user.username} | Error: {type(e).__name__} | Reason: {str(e)}")
        raise

# @router.get("/transaction/{transaction_id}")
# async def get_transaction_details(
#     transaction_id: int,
#     session: AsyncSessionDep,
#     current_user: User = Depends(get_current_user)
# ):
#     """Get detailed information about a specific transaction"""
#     try:
#         transaction = await session.get(Transaction, transaction_id)
        
#         if not transaction:
#             raise TransactionNotFoundException
        
#         # Verify the transaction belongs to the current user
#         if transaction.user_id != current_user.id:
#             raise UnauthorizedException(
#                 detail="Access denied to this transaction"
#             )
        
#         # Get reference user name if it's a transfer
#         reference_user_name = None
#         if transaction.reference_user_id:
#             reference_user = await session.get(User, transaction.reference_user_id)
#             reference_user_name = reference_user.username if reference_user else None
        
#         return {
#             "id": transaction.id,
#             "amount": f"{transaction.amount:.2f}",
#             "transaction_type": transaction.transaction_type.value,
#             "description": transaction.description,
#             "timestamp": transaction.timestamp.isoformat(),
#             "reference_user_name": reference_user_name
#         }
#     except Exception as e:
#         logger.error(f"Get transaction details failed for user {current_user.username} | Error: {type(e).__name__} | Reason: {str(e)}")
#         raise

@router.post("/qrcode/request")
async def qrcode_request(
    collect: PaymentCollectionRequest,
    session: AsyncSessionDep,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        t = datetime.now()
        expire_at = min(
            collect.expire or t + settings.qr_alive_delta,
            t + settings.qr_alive_delta
        )
        qrcode = QRCode(
            qr_id=str(uuid4()),
            qr_type=QRType.REQUEST_PAYMENT,
            amount=collect.amount,
            max_use_count=collect.max_usercount,
            expire=expire_at
        )
        session.add(qrcode)
        await session.commit()
        await session.refresh(qrcode)

        origin = request.headers.get("origin")
        url: str = f"{origin}/pay/request/{qrcode.qr_id}" if origin else f"/pay/request/{qrcode.qr_id}"

        qr_img = create_qr_code(url)
        return Response(
            content=qr_img,
            media_type="image/png",
            headers={
                "qr_id": qrcode.qr_id,
                "qr_url": url,
                "qr_type": qrcode.qr_type.value,
            }   
        )
    except Exception as e:
        logger.error(f"QR code request failed for user {current_user.username} | Error: {type(e).__name__} | Reason: {str(e)}")
        await session.rollback()
        raise

@router.post("/qrcode/send")
async def qrcode_send(
    qr: QRRequest,
    session: AsyncSessionDep,
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Response:
    try:
        qrcode = QRCode(
            qr_id=str(uuid4()),
            qr_type=QRType.SEND_PAYMENT,
            max_use_count=1,
            expire=datetime.now() + timedelta(minutes=1)
        )
        await qrcode.clean_unused_send_qrcodes(session)
        session.add(qrcode)
        await session.commit()
        await session.refresh(qrcode)

        origin = request.headers.get("origin")
        url: str = f"{origin}/pay/scan/{qrcode.qr_id}" if origin else f"/pay/scan/{qrcode.qr_id}"
        
        qr_img = create_qr_code(url)
        return Response(
            content=qr_img,
            media_type="image/png",
            headers={
                "qr_id": qrcode.qr_id,
                "qr_url": url,
                "qr_type": qrcode.qr_type.value,
            }   
        )
    except Exception as e:
        logger.error(f"QR code send failed for user {current_user.username} | Error: {type(e).__name__} | Reason: {str(e)}")
        await session.rollback()
        raise

@router.get("/qrcode/uuid/{qr_id}", response_model=QRCodeResponse)
async def get_qrcode_by_uuid(
    qr_id: str,
    session: AsyncSessionDep,
    current_user: User = Depends(get_current_user)
) -> QRCodeResponse:
    try:
        qrcode = await QRCode.get_by_qr_id(session, qr_id)
        if not qrcode:
            raise TransactionNotFoundException("QR code not found")
        
        if qrcode.qr_type == QRType.SEND_PAYMENT and not qrcode.can_be_used():
            raise TransactionNotFoundException("QR code has expired or is invalid")
        
        return QRCodeResponse(
            qr_id=qrcode.qr_id,
            qr_type=qrcode.qr_type.value,
            amount=qrcode.amount,
            expire=qrcode.expire.isoformat() if qrcode.expire else None
        )
    except Exception as e:
        logger.error(f"Get QR code by UUID failed for user {current_user.username} | Error: {type(e).__name__} | Reason: {str(e)}")
        raise