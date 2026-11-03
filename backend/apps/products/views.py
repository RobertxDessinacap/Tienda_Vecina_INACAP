from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from apps.products.models import Product, Category
from apps.products.serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    CategorySerializer
)
from apps.accounts.permissions import IsSellerOrAdmin, IsAccountOwnerOrReadOnly

class CategoryListView(APIView):
    """Public listing of all product categories."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.all().order_by('name')
        serializer = CategorySerializer(categories, many=True)
        return Response({"status": "success", "data": serializer.data})


class ProductListCreateView(APIView):
    """
    Catalog View:
    - GET: Public browsing, search, and category filtering.
    - POST: Restricted by RBAC (ISO 27001). ONLY Sellers and Admins can create products.
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsSellerOrAdmin()]
        return [permissions.AllowAny()]

    def get(self, request):
        queryset = Product.objects.select_related('category', 'seller_account').all()

        # Search parameter ?q=
        search_query = request.query_params.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        # Filter by Category ?category=
        category_param = request.query_params.get('category', '').strip()
        if category_param:
            queryset = queryset.filter(
                Q(category__slug=category_param) | Q(category__id__iexact=category_param)
            )

        # Sort order ?ordering=
        ordering = request.query_params.get('ordering', '-created_at')
        if ordering == 'price_asc':
            queryset = queryset.order_by('price')
        elif ordering == 'price_desc':
            queryset = queryset.order_by('-price')
        elif ordering == 'rating':
            queryset = queryset.order_by('-rating')
        else:
            queryset = queryset.order_by('-created_at')

        serializer = ProductSerializer(queryset, many=True)
        return Response({
            "status": "success",
            "count": queryset.count(),
            "data": serializer.data
        })

    def post(self, request):
        serializer = ProductCreateUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response({
                "status": "success",
                "message": "Producto publicado exitosamente en el catálogo.",
                "data": ProductSerializer(product).data
            }, status=status.HTTP_201_CREATED)
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    """
    Single Product View:
    - GET: Public product details.
    - PUT / DELETE: Protected. Only the seller owning the Intermediate Account can modify.
    """
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAccountOwnerOrReadOnly()]

    def get_object(self, pk):
        try:
            return Product.objects.select_related('category', 'seller_account').get(id=pk)
        except (Product.DoesNotExist, ValueError):
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response({"status": "success", "data": serializer.data})

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, product)

        serializer = ProductCreateUpdateSerializer(product, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            updated_product = serializer.save()
            return Response({
                "status": "success",
                "message": "Producto actualizado exitosamente.",
                "data": ProductSerializer(updated_product).data
            })
        return Response({"status": "fail", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"status": "error", "message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, product)
        product.delete()
        return Response({
            "status": "success",
            "message": "Producto eliminado exitosamente del catálogo."
        }, status=status.HTTP_200_OK)
