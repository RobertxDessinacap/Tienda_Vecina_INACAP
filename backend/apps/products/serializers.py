import re
from rest_framework import serializers
from django.utils.html import escape
from apps.products.models import Product, Category
from apps.accounts.serializers import UserProfileSerializer
from apps.products.utils import process_and_secure_product_image

FORBIDDEN_XSS_REGEX = re.compile(r'[<>{}\[\]*\\;^$|~`]')
MALICIOUS_SCRIPT_PATTERNS = re.compile(r'(javascript:|data:|vbscript:|on\w+=|<\s*script|<\s*iframe|<\s*embed|<\s*object)', re.IGNORECASE)

def validate_xss_safe(text, field_name):
    if not text:
        return text
    if FORBIDDEN_XSS_REGEX.search(text):
        raise serializers.ValidationError(
            f"El campo '{field_name}' contiene caracteres especiales no permitidos por seguridad anti-XSS ([ ] {{ }} * < > \\ ; etc.)."
        )
    if MALICIOUS_SCRIPT_PATTERNS.search(text):
        raise serializers.ValidationError(
            f"El campo '{field_name}' contiene secuencias no permitidas (script o inyección detectada)."
        )
    return text.strip()

class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon_name', 'products_count']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    seller_alias = serializers.CharField(source='seller_profile.public_alias', read_only=True)
    # Nombre del usuario que ingresó (obtenido desde Persona -> UserProfile)
    seller_nombre = serializers.CharField(source='seller_profile.persona.nombre_completo', read_only=True)
    seller_reputation = serializers.FloatField(source='seller_profile.reputation_score', read_only=True)
    seller = UserProfileSerializer(source='seller_profile', read_only=True)
    is_official_store = serializers.BooleanField(source='seller_profile.is_official_store', read_only=True)
    seller_official_store_name = serializers.CharField(source='seller_profile.official_store_name', read_only=True)
    seller_official_store_url = serializers.CharField(source='seller_profile.official_store_url', read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    display_image_url = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'caracteristicas_ads',
            'price',
            'original_price',
            'discount_percentage',
            'stock',
            'category',
            'category_name',
            'image',
            'image_url',
            'display_image_url',
            'free_shipping',
            'installments',
            'seller',
            'seller_alias',
            'seller_nombre',
            'seller_reputation',
            'is_official_store',
            'seller_official_store_name',
            'seller_official_store_url',
            'rating',
            'reviews_count',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'seller', 'rating', 'reviews_count', 'created_at', 'display_image_url']


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador de creación con validaciones estrictas requeridas por el profesor:
    - Características ADS con + de 250 caracteres.
    - Imagen validada por extensión y formato real, normalizada a 900x600 y <= 1 MB.
    """
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            'title',
            'description',
            'caracteristicas_ads',
            'price',
            'original_price',
            'stock',
            'category',
            'image_url',
            'image_file',
            'free_shipping',
            'installments',
        ]

    def validate_title(self, value):
        cleaned = validate_xss_safe(value, "Nombre del Producto")
        if len(cleaned) < 3:
            raise serializers.ValidationError("El nombre del producto debe tener al menos 3 caracteres.")
        return cleaned

    def validate_description(self, value):
        return validate_xss_safe(value, "Descripción")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser un valor positivo mayor a 0.")
        return value

    def validate_caracteristicas_ads(self, value):
        cleaned = validate_xss_safe(value, "Características ADS")
        # Validación explícita: "+ de 250 caracteres"
        if len(cleaned) <= 250:
            raise serializers.ValidationError(
                f"Las características en ADS deben contener MÁS DE 250 caracteres (actual: {len(cleaned)} caracteres)."
            )
        return cleaned

    def create(self, validated_data):
        request = self.context.get('request')
        image_file = validated_data.pop('image_file', None)

        # Procesamiento y blindaje de la imagen a 900x600 y max 1 MB
        processed_image = None
        if image_file:
            processed_image = process_and_secure_product_image(image_file)

        # Asignación al UserProfile del usuario vendedor
        seller_profile = request.user.user_profile
        product = Product.objects.create(
            seller_profile=seller_profile,
            image=processed_image,
            **validated_data
        )
        return product

    def update(self, instance, validated_data):
        from django.utils.text import slugify
        image_file = validated_data.pop('image_file', None)
        if image_file:
            instance.image = process_and_secure_product_image(image_file)

        old_title = instance.title
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Si el título cambió, recalcular URL limpia (slug)
        if 'title' in validated_data and validated_data['title'] != old_title:
            base_slug = slugify(instance.title) or 'producto'
            potential_slug = base_slug
            counter = 1
            while Product.objects.filter(slug=potential_slug).exclude(id=instance.id).exists():
                potential_slug = f"{base_slug}-{counter}"
                counter += 1
            instance.slug = potential_slug

        instance.save()
        return instance


class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Serializador para que los compradores evalúen un pedido / producto.
    """
    buyer_alias = serializers.CharField(source='user_profile.public_alias', read_only=True)

    class Meta:
        from apps.products.models import ProductReview
        model = ProductReview
        fields = ['id', 'rating', 'comment', 'buyer_alias', 'created_at']
        read_only_fields = ['id', 'buyer_alias', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La valoración debe ser un número entero de 1 a 5 estrellas.")
        return value

    def validate_comment(self, value):
        return validate_xss_safe(value, "Comentario de Evaluación")
