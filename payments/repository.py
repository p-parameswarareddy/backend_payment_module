import uuid
from django.db import transaction
from .db import get_cursor, execute_query
from django.db import IntegrityError as DjangoIntegrityError


def get_payment_by_idempotency_key(idempotency_key):
    return execute_query(
        "SELECT * FROM payments WHERE idempotency_key = %s",
        [idempotency_key],
        fetch="one"
    )


def get_successful_payment_for_order(order_id):
    return execute_query(
        "SELECT * FROM payments WHERE order_id = %s AND status = 'SUCCESS'",
        [order_id],
        fetch="one"
    )


def get_payment_by_id(payment_id):
    return execute_query(
        "SELECT * FROM payments WHERE id = %s",
        [payment_id],
        fetch="one"
    )


def get_payments_by_order_id(order_id):
    return execute_query(
        "SELECT * FROM payments WHERE order_id = %s ORDER BY created_at DESC",
        [order_id],
        fetch="all"
    )


def create_payment(order_id, idempotency_key, amount_in_subunits, currency):
    payment_id = str(uuid.uuid4())

    with transaction.atomic():
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO payments
                    (id, order_id, idempotency_key, amount_in_subunits, currency)
                VALUES
                    (%s, %s, %s, %s, %s)
                RETURNING *
            """, [payment_id, order_id, idempotency_key, amount_in_subunits, currency])

            row = dict(cur.fetchone())
            row["amount_in_subunits"] = int(row["amount_in_subunits"])
            return row

def update_payment_status(payment_id, new_status, failure_reason=None):
    from psycopg2 import errors as pg_errors

    with transaction.atomic():
        with get_cursor() as cur:

            
            cur.execute(
                "SELECT * FROM payments WHERE id = %s FOR UPDATE",
                [payment_id]
            )
            row = cur.fetchone()

            if row is None:
                raise ValueError(f"Payment '{payment_id}' not found.")

            current_status = row["status"]

            
            allowed = {
                "PENDING": {"SUCCESS", "FAILED"},
                "SUCCESS": {"REFUNDED"},
            }
            if new_status not in allowed.get(current_status, set()):
                raise ValueError(
                    f"Cannot transition from '{current_status}' to '{new_status}'."
                )

            try:
                cur.execute("""
                    UPDATE payments
                    SET    status = %s,
                           failure_reason = COALESCE(%s, failure_reason)
                    WHERE  id = %s
                    RETURNING *
                """, [new_status, failure_reason, payment_id])

            except pg_errors.UniqueViolation:
                
                raise ValueError(
                    f"Order already has a successful payment. "
                    f"Cannot mark another payment as SUCCESS."
                )
            except DjangoIntegrityError:
                raise ValueError(
                    f"Order already has a successful payment. "
                    f"Cannot mark another payment as SUCCESS."
                )



            updated = dict(cur.fetchone())
            updated["amount_in_subunits"] = int(updated["amount_in_subunits"])
            return updated

def create_refund(payment_id, amount_in_subunits, reason=None):
    refund_id = str(uuid.uuid4())

    with transaction.atomic():
        with get_cursor() as cur:

            
            cur.execute(
                "SELECT * FROM payments WHERE id = %s FOR UPDATE",
                [payment_id]
            )
            payment = cur.fetchone()

            if payment is None:
                raise ValueError(f"Payment '{payment_id}' not found.")

            if payment["status"] != "SUCCESS":
                raise ValueError(
                    f"Only SUCCESS payments can be refunded. "
                    f"Current status: '{payment['status']}'."
                )

            if amount_in_subunits > int(payment["amount_in_subunits"]):
                raise ValueError(
                    f"Refund amount {amount_in_subunits} exceeds "
                    f"payment amount {payment['amount_in_subunits']}."
                )

            
            cur.execute("""
                INSERT INTO refunds
                    (id, payment_id, amount_in_subunits, reason, status)
                VALUES
                    (%s, %s, %s, %s, 'SUCCESS')
                RETURNING *
            """, [refund_id, payment_id, amount_in_subunits, reason])

            refund = dict(cur.fetchone())
            refund["amount_in_subunits"] = int(refund["amount_in_subunits"])

            
            cur.execute("""
                UPDATE payments SET status = 'REFUNDED'
                WHERE id = %s
            """, [payment_id])

            return refund