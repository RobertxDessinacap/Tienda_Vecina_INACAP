from django.urls import path
from apps.products.views import (
    ProductListCreateView,
    ProductDetailView,
    CategoryListView,
    MyProductsView,
    ProductReviewView
)

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('my-products/', MyProductsView.as_view(), name='my-products'),
    path('<str:lookup>/review/', ProductReviewView.as_view(), name='product-review'),
    path('<str:lookup>/', ProductDetailView.as_view(), name='product-detail-clean-url'),
]
