from rest_framework import serializers
from apps.products.models import Product, Category
from apps.accounts.serializers import AccountProxyPublicSerializer

class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon_name', 'products_count']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_alias = serializers.CharField(source='seller_account.public_alias', read_only=True)
    seller_reputation = serializers.FloatField(source='seller_account.reputation_score', read_only=True)
    seller = AccountProxyPublicSerializer(source='seller_account', read_only=True)
    discount_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'price',
            'original_price',
            'discount_percentage',
            'stock',
            'category',
            'category_name',
            'image_url',
            'free_shipping',
            'installments',
            'seller',
            'seller_alias',
            'seller_reputation',
            'rating',
            'reviews_count',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'seller', 'rating', 'reviews_count', 'created_at']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer used exclusively for creating and updating products.
    Enforces business logic, positive pricing and auto-attaches Intermediate Account.
    """
    class Meta:
        model = Product
        fields = [
            'title',
            'description',
            'price',
            'original_price',
            'stock',
            'category',
            'image_url',
            'free_shipping',
            'installments',
        ]

    def validate_title(self, value):
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise serializers.ValidationError("El título debe tener al menos 3 caracteres.")
        return cleaned

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        # Crucial security link: Attach product to Intermediate Account (AccountProxy)
        # Never store raw user credential ID in product record
        seller_account = request.user.intermediate_account
        product = Product.objects.create(
            seller_account=seller_account,
            **validated_data
        )
        return product
