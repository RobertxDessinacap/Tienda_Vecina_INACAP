from django.urls import path
from apps.payments.views import (
    CartCalculateAPIView,
    TransbankInitAPIView,
    TransbankCommitAPIView,
    PaymentMethodsAPIView
)

urlpatterns = [
    path('cart/calculate/', CartCalculateAPIView.as_view(), name='cart-calculate'),
    path('transbank/init/', TransbankInitAPIView.as_view(), name='transbank-init'),
    path('transbank/commit/', TransbankCommitAPIView.as_view(), name='transbank-commit'),
    path('methods/', PaymentMethodsAPIView.as_view(), name='payment-methods'),
]
