# -*- coding: utf-8 -*-
"""
Einziger Ort, an dem sich Customer.balance_cents aendert. Jede Aenderung
erzeugt IMMER einen WalletTransaction-Ledger-Eintrag in derselben DB-
Transaktion - balance_cents und Ledger koennen dadurch nie auseinanderlaufen.
"""
from app.extensions import db
from app.models import Customer, WalletTransaction, WalletTransactionType


class InsufficientBalance(Exception):
    pass


def top_up(customer: Customer, amount_cents: int, payment_method: str,
           reference: str = None) -> WalletTransaction:
    if amount_cents <= 0:
        raise ValueError("amount_cents muss positiv sein")

    customer.balance_cents += amount_cents
    tx = WalletTransaction(
        customer_id=customer.id,
        amount_cents=amount_cents,
        balance_after_cents=customer.balance_cents,
        type=WalletTransactionType.TOPUP,
        payment_method=payment_method,
        reference=reference,
    )
    db.session.add(tx)
    db.session.commit()
    return tx


def charge(customer: Customer, amount_cents: int, note: str = None) -> WalletTransaction:
    if amount_cents <= 0:
        raise ValueError("amount_cents muss positiv sein")
    if customer.balance_cents < amount_cents:
        raise InsufficientBalance(
            f"Guthaben {customer.balance_cents} reicht nicht fuer {amount_cents}"
        )

    customer.balance_cents -= amount_cents
    tx = WalletTransaction(
        customer_id=customer.id,
        amount_cents=-amount_cents,
        balance_after_cents=customer.balance_cents,
        type=WalletTransactionType.WASH_CHARGE,
        note=note,
    )
    db.session.add(tx)
    db.session.commit()
    return tx


def refund(customer: Customer, amount_cents: int, note: str = None) -> WalletTransaction:
    if amount_cents <= 0:
        raise ValueError("amount_cents muss positiv sein")

    customer.balance_cents += amount_cents
    tx = WalletTransaction(
        customer_id=customer.id,
        amount_cents=amount_cents,
        balance_after_cents=customer.balance_cents,
        type=WalletTransactionType.REFUND,
        note=note,
    )
    db.session.add(tx)
    db.session.commit()
    return tx


def admin_adjustment(customer: Customer, amount_cents: int, note: str) -> WalletTransaction:
    """amount_cents kann positiv (Gutschrift) oder negativ (Korrektur nach unten) sein."""
    if amount_cents == 0:
        raise ValueError("amount_cents darf nicht 0 sein")
    if customer.balance_cents + amount_cents < 0:
        raise InsufficientBalance("Korrektur wuerde Guthaben negativ machen")

    customer.balance_cents += amount_cents
    tx = WalletTransaction(
        customer_id=customer.id,
        amount_cents=amount_cents,
        balance_after_cents=customer.balance_cents,
        type=WalletTransactionType.ADMIN_ADJUSTMENT,
        payment_method="admin",
        note=note,
    )
    db.session.add(tx)
    db.session.commit()
    return tx
