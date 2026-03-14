from django.db import IntegrityError
from . import repository


class PaymentService:

    VALID_CURRENCIES   = {"INR", "USD", "EUR", "GBP"}
    VALID_NEW_STATUSES = {"SUCCESS", "FAILED"}

    def record_payment(self, data):
        
        required = ["order_id", "idempotency_key", "amount_in_subunits", "currency"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        
        try:
            amount_in_subunits = int(data["amount_in_subunits"])
        except (ValueError, TypeError):
            raise ValueError("amount_in_subunits must be an integer. e.g. 49999 for ₹499.99")
        if amount_in_subunits <= 0:
            raise ValueError("amount_in_subunits must be greater than zero.")

        
        currency = data["currency"].upper()
        if currency not in self.VALID_CURRENCIES:
            raise ValueError(f"Unsupported currency. Allowed: {sorted(self.VALID_CURRENCIES)}")

        order_id        = str(data["order_id"]).strip()
        idempotency_key = str(data["idempotency_key"]).strip()

        
        existing = repository.get_payment_by_idempotency_key(idempotency_key)
        if existing:
            return existing, False

        
        if repository.get_successful_payment_for_order(order_id):
            raise ValueError(f"Order '{order_id}' already has a successful payment.")

        
        try:
            payment = repository.create_payment(
                order_id=order_id,
                idempotency_key=idempotency_key,
                amount_in_subunits=amount_in_subunits,
                currency=currency,
            )
        except IntegrityError:
            existing = repository.get_payment_by_idempotency_key(idempotency_key)
            if existing:
                return existing, False
            raise RuntimeError("DB conflict while creating payment.")

        return payment, True

    def update_payment_status(self, payment_id, data):
        
        new_status = data.get("status", "").upper()
        if not new_status:
            raise ValueError("'status' field is required.")
        if new_status not in self.VALID_NEW_STATUSES:
            raise ValueError(f"status must be one of {sorted(self.VALID_NEW_STATUSES)}.")

        failure_reason = data.get("failure_reason") if new_status == "FAILED" else None

        return repository.update_payment_status(
            payment_id=payment_id,
            new_status=new_status,
            failure_reason=failure_reason,
        )

    def fetch_payments_for_order(self, order_id):
        if not order_id:
            raise ValueError("order_id is required.")
        return repository.get_payments_by_order_id(order_id)

    def refund_payment(self, payment_id, data):
        
        raw = data.get("amount_in_subunits")
        if raw is None:
            raise ValueError("'amount_in_subunits' is required for refund.")
        try:
            amount_in_subunits = int(raw)
        except (ValueError, TypeError):
            raise ValueError("amount_in_subunits must be an integer.")
        if amount_in_subunits <= 0:
            raise ValueError("Refund amount must be greater than zero.")

        reason = data.get("reason")

        return repository.create_refund(
            payment_id=payment_id,
            amount_in_subunits=amount_in_subunits,
            reason=reason,
        )