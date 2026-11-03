from django.urls import path
from apps.products.views import ProductListCreateView, ProductDetailView, CategoryListView

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
