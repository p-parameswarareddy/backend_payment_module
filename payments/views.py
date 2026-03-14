from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import PaymentService
from . import repository

payment_service = PaymentService()


class PaymentListCreateView(APIView):
    """POST /api/payments/ — Record a new payment"""

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response({"success": False, "error": "Request body must be JSON."}, status=400)

        try:
            payment, created = payment_service.record_payment(request.data)
        except ValueError as e:
            return Response({"success": False, "error": str(e)}, status=422)
        except RuntimeError as e:
            return Response({"success": False, "error": str(e)}, status=409)

        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        message = "Payment recorded." if created else "Duplicate request, returning existing payment."

        return Response({"success": True, "message": message, "data": payment}, status=http_status)


class PaymentDetailView(APIView):
    """
    GET   /api/payments/<payment_id>/ — Fetch a payment
    PATCH /api/payments/<payment_id>/ — Update payment status
    """

    def get(self, request, payment_id):
        payment = repository.get_payment_by_id(payment_id)
        if not payment:
            return Response({"success": False, "error": f"Payment '{payment_id}' not found."}, status=404)
        return Response({"success": True, "data": payment})

    def patch(self, request, payment_id):
        if not isinstance(request.data, dict):
            return Response({"success": False, "error": "Request body must be JSON."}, status=400)

        try:
            payment = payment_service.update_payment_status(payment_id, request.data)
        except ValueError as e:
            msg = str(e)
            http_status = 404 if "not found" in msg.lower() else 422
            return Response({"success": False, "error": msg}, status=http_status)

        return Response({"success": True, "message": "Payment status updated.", "data": payment})


class OrderPaymentsView(APIView):
    """GET /api/orders/<order_id>/payments/ — Fetch all payments for an order"""

    def get(self, request, order_id):
        try:
            payments = payment_service.fetch_payments_for_order(order_id)
        except ValueError as e:
            return Response({"success": False, "error": str(e)}, status=422)

        return Response({
            "success": True,
            "data": {
                "order_id": order_id,
                "count": len(payments),
                "payments": payments
            }
        })


class PaymentRefundView(APIView):
    """POST /api/payments/<payment_id>/refund/ — Refund a payment"""

    def post(self, request, payment_id):
        if not isinstance(request.data, dict):
            return Response({"success": False, "error": "Request body must be JSON."}, status=400)

        try:
            refund = payment_service.refund_payment(payment_id, request.data)
        except ValueError as e:
            msg = str(e)
            http_status = 404 if "not found" in msg.lower() else 422
            return Response({"success": False, "error": msg}, status=http_status)

        return Response({
            "success": True,
            "message": "Refund successful.",
            "data": refund
        }, status=201)