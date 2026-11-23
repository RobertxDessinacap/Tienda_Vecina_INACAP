import html
import re
import uuid
from urllib.parse import unquote
from django.db import IntegrityError
from django.db.models import Q, Min, Max
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsSellerOrAdmin, IsAccountOwnerOrReadOnly
from apps.payments.models import OrderItem
from apps.products.models import Product, Category, ProductReview
from apps.products.serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ProductReviewSerializer,
    CategorySerializer
)


class StandardCatalogPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 48

    def get_paginated_response(self, data, price_bounds=None):
        return Response({
            "status": "success",
            "count": self.page.paginator.count,
            "page": self.page.number,
            "total_pages": self.page.paginator.num_pages,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "price_bounds": price_bounds or {"min": 0, "max": 2500000},
            "data": data,
        })


def _sanitize_search_query(raw_query: str) -> str:
    """
    Sanitiza el parámetro de búsqueda ?q= eliminando etiquetas HTML (<, >) y patrones de scripts,
    permitiendo caracteres comerciales legítimos como $, *, [, ], ;, %, etc.
    """
    if not raw_query:
        return ''
    cleaned = raw_query.strip()
    prev = None
    for _ in range(10):
        if cleaned == prev:
            break
        prev = cleaned
        decoded = html.unescape(unquote(cleaned))
        decoded = re.sub(r'[\x00-\x1f\x7f]+', '', decoded)
        decoded = re.sub(r'<\s*/?\s*script\b[^>]*>', '', decoded, flags=re.IGNORECASE)
        decoded = re.sub(r'[<>]', '', decoded)
        decoded = re.sub(
            r'(?:javascript\s*:|vbscript\s*:|data\s*:\s*text/html|\bon[a-z]+\s*=)',
            '',
            decoded,
            flags=re.IGNORECASE
        )
        cleaned = decoded.strip()
    return cleaned


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
    - GET: Búsqueda, filtrado, ordenamiento y paginación pública.
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
            clean_search = _sanitize_search_query(search_query)
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
            queryset = queryset.order_by('price', 'id')
        elif ordering == 'price_desc':
            queryset = queryset.order_by('-price', 'id')
        elif ordering == 'rating':
            queryset = queryset.order_by('-rating', 'id')
        else:
            queryset = queryset.order_by('-created_at', 'id')

        # Rangos globales de precio para sliders de filtrado
        price_bounds_agg = Product.objects.aggregate(
            min_catalog_price=Min('price'),
            max_catalog_price=Max('price')
        )
        price_bounds = {
            "min": float(price_bounds_agg['min_catalog_price'] or 0),
            "max": float(price_bounds_agg['max_catalog_price'] or 2500000)
        }

        paginator = StandardCatalogPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data, price_bounds=price_bounds)

        serializer = ProductSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "count": queryset.count(),
            "page": 1,
            "total_pages": 1,
            "next": None,
            "previous": None,
            "price_bounds": price_bounds,
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

    def patch(self, request, lookup):
        return self.put(request, lookup)

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


class MyProductsView(APIView):
    """
    Vista única para Vendedores: Lista exclusivamente los productos publicados
    por el usuario autenticado (su UserProfile).
    """
    permission_classes = [permissions.IsAuthenticated, IsSellerOrAdmin]

    def get(self, request):
        user_profile = getattr(request.user, 'user_profile', None)
        if not user_profile:
            return Response({"status": "fail", "message": "Perfil de vendedor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        products = Product.objects.filter(seller_profile=user_profile).select_related(
            'category', 'seller_profile', 'seller_profile__persona'
        ).order_by('-created_at')

        serializer = ProductSerializer(products, many=True)
        return Response({
            "status": "success",
            "count": products.count(),
            "data": serializer.data
        })


class ProductReviewView(APIView):
    """
    Permite a compradores verificados evaluar un producto adquirido y consultar opiniones.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_product(self, lookup):
        try:
            val_uuid = uuid.UUID(str(lookup))
            return Product.objects.filter(id=val_uuid).first()
        except ValueError:
            return Product.objects.filter(slug=lookup).first()

    def get(self, request, lookup):
        product = self.get_product(lookup)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        reviews = product.reviews.select_related('user_profile').order_by('-created_at')
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response({
            "status": "success",
            "count": reviews.count(),
            "rating": product.rating,
            "reviews_count": product.reviews_count,
            "data": serializer.data
        })

    def post(self, request, lookup):
        product = self.get_product(lookup)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user_profile = getattr(request.user, 'user_profile', None)
        if not user_profile:
            return Response(
                {"status": "fail", "message": "Perfil de usuario no encontrado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.seller_profile_id == user_profile.id:
            return Response(
                {"status": "fail", "message": "No puedes evaluar tus propios productos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        has_purchased = OrderItem.objects.filter(
            order__buyer_profile=user_profile,
            order__status='AUTHORIZED',
            product=product
        ).exists()
        if not has_purchased:
            return Response(
                {
                    "status": "fail",
                    "message": "Solo compradores que hayan adquirido este producto pueden emitir una evaluación."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if ProductReview.objects.filter(product=product, user_profile=user_profile).exists():
            return Response(
                {"status": "fail", "message": "Ya has evaluado este producto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            try:
                review = ProductReview.objects.create(
                    product=product,
                    user_profile=user_profile,
                    rating=serializer.validated_data['rating'],
                    comment=serializer.validated_data.get('comment', '')
                )
            except IntegrityError:
                return Response(
                    {"status": "fail", "message": "Ya has evaluado este producto."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product.refresh_from_db()
            return Response({
                "status": "success",
                "message": "¡Evaluación registrada exitosamente!",
                "data": {
                    "review": ProductReviewSerializer(review).data,
                    "updated_rating": product.rating,
                    "reviews_count": product.reviews_count
                }
            }, status=status.HTTP_201_CREATED)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
