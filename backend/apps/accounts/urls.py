from django.urls import path
from apps.accounts.views import (
    RegisterAPIView,
    LoginAPIView,
    MeAPIView,
    UpgradeToSellerAPIView,
    RegisterStoreAPIView
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='auth-register'),
    path('login/', LoginAPIView.as_view(), name='auth-login'),
    path('me/', MeAPIView.as_view(), name='auth-me'),
    path('upgrade-seller/', UpgradeToSellerAPIView.as_view(), name='auth-upgrade-seller'),
    path('register-store/', RegisterStoreAPIView.as_view(), name='auth-register-store'),
]
