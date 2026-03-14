from django.urls import path
from .views import (
    PaymentListCreateView,
    PaymentDetailView,
    OrderPaymentsView,
    PaymentRefundView,
)

urlpatterns = [
    path("payments/", PaymentListCreateView.as_view(), name="payment-create"),
    path("payments/<str:payment_id>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("payments/<str:payment_id>/refund/", PaymentRefundView.as_view(), name="payment-refund"),
    path("orders/<str:order_id>/payments/", OrderPaymentsView.as_view(), name="order-payments"),
]