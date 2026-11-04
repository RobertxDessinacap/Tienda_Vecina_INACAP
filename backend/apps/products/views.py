from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q, Min, Max
from django.utils.html import escape
import uuid
import re
from apps.products.models import Product, Category
from apps.products.serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    CategorySerializer
)
from apps.accounts.permissions import IsSellerOrAdmin, IsAccountOwnerOrReadOnly

class CategoryListView(APIView):
    """Listado público de categorías."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.all().order_by('name')
        serializer = CategorySerializer(categories, many=True)
        return Response({"status": "success", "data": serializer.data})


class ProductListCreateView(APIView):
    """
    Catálogo:
    - GET: Búsqueda, filtrado y ordenamiento público.
    - POST: Exclusivo para VENDEDORES y ADMINS (RBAC).
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsSellerOrAdmin()]
        return [permissions.AllowAny()]

    def get(self, request):
        queryset = Product.objects.select_related('category', 'seller_profile', 'seller_profile__persona').all()

        search_query = request.query_params.get('q', '').strip()
        if search_query:
            # Sanitización rigurosa anti-XSS e inyección de caracteres (OWASP)
            clean_search = re.sub(r'[<>{}\[\]*\\;^$|~`]', '', search_query).strip()
            if clean_search:
                queryset = queryset.filter(
                    Q(title__icontains=clean_search) |
                    Q(description__icontains=clean_search) |
                    Q(caracteristicas_ads__icontains=clean_search) |
                    Q(category__name__icontains=clean_search)
                )

        category_param = request.query_params.get('category', '').strip()
        if category_param:
            queryset = queryset.filter(
                Q(category__slug=category_param) | Q(category__id__iexact=category_param)
            )

        min_price = request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass

        max_price = request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass

        free_shipping = request.query_params.get('free_shipping')
        if free_shipping in ('true', '1', 'True'):
            queryset = queryset.filter(free_shipping=True)

        ordering = request.query_params.get('ordering', '-created_at')
        if ordering == 'price_asc':
            queryset = queryset.order_by('price')
        elif ordering == 'price_desc':
            queryset = queryset.order_by('-price')
        elif ordering == 'rating':
            queryset = queryset.order_by('-rating')
        else:
            queryset = queryset.order_by('-created_at')

        # Rangos globales de precio para sliders de filtrado
        price_bounds = Product.objects.aggregate(
            min_catalog_price=Min('price'),
            max_catalog_price=Max('price')
        )

        serializer = ProductSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "count": queryset.count(),
            "price_bounds": {
                "min": float(price_bounds['min_catalog_price'] or 0),
                "max": float(price_bounds['max_catalog_price'] or 2500000)
            },
            "data": serializer.data
        })

    def post(self, request):
        serializer = ProductCreateUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response({
                "status": "success",
                "message": "Producto publicado exitosamente con imagen procesada (900x600, <=1MB).",
                "data": ProductSerializer(product).data
            }, status=status.HTTP_201_CREATED)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    """
    Detalle de producto con URL limpia (soporta búsqueda por slug o por ID).
    """
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAccountOwnerOrReadOnly()]

    def get_object(self, lookup):
        queryset = Product.objects.select_related('category', 'seller_profile', 'seller_profile__persona')
        # Intentar buscar por UUID si es válido, o por URL limpia (slug)
        try:
            val_uuid = uuid.UUID(str(lookup))
            return queryset.filter(id=val_uuid).first()
        except ValueError:
            return queryset.filter(slug=lookup).first()

    def get(self, request, lookup):
        product = self.get_object(lookup)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response({"status": "success", "data": serializer.data})

    def put(self, request, lookup):
        product = self.get_object(lookup)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, product)

        serializer = ProductCreateUpdateSerializer(product, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_product = serializer.save()
            return Response({
                "status": "success",
                "message": "Producto actualizado con éxito.",
                "data": ProductSerializer(updated_product).data
            })
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, lookup):
        product = self.get_object(lookup)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, product)
        product.delete()
        return Response({
            "status": "success",
            "message": "Producto eliminado del catálogo."
        }, status=status.HTTP_200_OK)
