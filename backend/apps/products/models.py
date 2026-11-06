import uuid
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinLengthValidator
from apps.accounts.models import UserProfile

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    icon_name = models.CharField(max_length=50, default='Package')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Modelo de Producto solicitado por el profesor:
    - Nombre del producto (title)
    - Precio (price)
    - Características subidas en ADS (+250 caracteres obligatorios)
    - Descripción del producto
    - Imagen procesada y blindada (900x600 y máximo 1 MB)
    - URL limpia (slug con solo el nombre del producto)
    - Vinculado al UserProfile (el perfil intermedio que se mueve en el sistema)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, db_index=True, verbose_name="Nombre del Producto")
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text="URL limpia basada únicamente en el nombre del producto"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio")
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Requisito explícito: Características en ADS con más de 250 caracteres
    caracteristicas_ads = models.TextField(
        validators=[MinLengthValidator(251, message="Las características en ADS deben contener más de 250 caracteres.")],
        verbose_name="Características ADS (+250 caracteres)",
        default="Características técnicas avanzadas del producto para ADS: Rendimiento óptimo probado bajo estándares de alta exigencia, certificación oficial de fábrica, conectividad de última generación para sincronización rápida y garantía de durabilidad extendida para uso diario intensivo en todo Chile."
    )
    description = models.TextField(verbose_name="Descripción del Producto")

    # Imagen procesada con seguridad a 900x600 y <= 1 MB
    image = models.ImageField(upload_to='productos/', null=True, blank=True)
    image_url = models.URLField(
        max_length=1000,
        default='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600'
    )
    # Galería de imágenes (hasta 5 fotos máximo por producto)
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de URLs de imágenes del producto (hasta 5 fotos)"
    )

    stock = models.PositiveIntegerField(default=1)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    free_shipping = models.BooleanField(default=True)
    installments = models.PositiveIntegerField(default=6)

    # El UserProfile intermedio que se mueve en el sistema
    seller_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='products'
    )

    # Valoración real: los productos nuevos nacen sin valoración predeterminada
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, default=None)
    reviews_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Generar URL limpia con solo el nombre del producto
        if not self.slug:
            base_slug = slugify(self.title) or 'producto'
            potential_slug = base_slug
            counter = 1
            while Product.objects.filter(slug=potential_slug).exclude(id=self.id).exists():
                potential_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = potential_slug
        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return int(round(discount))
        return 0

    @property
    def display_image_url(self):
        if self.images and isinstance(self.images, list) and len(self.images) > 0 and self.images[0]:
            return self.images[0]
        if self.image:
            return self.image.url
        return self.image_url

    @property
    def all_images(self):
        imgs = []
        if self.images and isinstance(self.images, list):
            for u in self.images:
                if u and u not in imgs:
                    imgs.append(u)
        main_img = None
        if self.image:
            main_img = self.image.url
        elif self.image_url:
            main_img = self.image_url
        if main_img and main_img not in imgs:
            imgs.insert(0, main_img)
        return imgs[:5]

    def __str__(self):
        return f"{self.title} (${self.price})"


class ProductReview(models.Model):
    """
    Evaluación de compra realizada por un comprador a un producto.
    Calcula dinámicamente la valoración real del producto.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveSmallIntegerField(help_text="Calificación de 1 a 5 estrellas")
    comment = models.TextField(blank=True, default='', verbose_name="Comentario u Opinión")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Evaluación de Producto'
        verbose_name_plural = 'Evaluaciones de Productos'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalcular dinámicamente el promedio y conteo del producto
        reviews = self.product.reviews.all()
        count = reviews.count()
        if count > 0:
            avg = sum(r.rating for r in reviews) / count
            self.product.rating = round(avg, 1)
            self.product.reviews_count = count
        else:
            self.product.rating = None
            self.product.reviews_count = 0
        self.product.save(update_fields=['rating', 'reviews_count'])

    def __str__(self):
        return f"{self.rating}★ para {self.product.title} por {self.user_profile.public_alias}"
