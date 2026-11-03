from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import UserCredential
from apps.products.models import Category, Product
from apps.accounts.authentication import generate_jwt_token

class ProductProfRequirementsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Computación')

        self.seller = UserCredential.objects.create_user(
            email='vendedor_api@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_SELLER
        )
        self.seller_token = generate_jwt_token(self.seller)

        self.buyer = UserCredential.objects.create_user(
            email='comprador_api@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_BUYER
        )
        self.buyer_token = generate_jwt_token(self.buyer)

        # Texto válido de ADS (+250 caracteres)
        self.valid_ads_text = (
            "ESPECIFICACIONES ADS OFICIALES DE ALTO RENDIMIENTO: "
            "Procesador multinúcleo de arquitectura de 4 nanómetros, memoria unificada de alta velocidad "
            "con tasa de transferencia récord en la industria, chasis resistente a impactos y certificación de "
            "garantía oficial en todo el territorio nacional con soporte prioritario 24/7."
        )

    def test_caracteristicas_ads_min_length_validation(self):
        """Requisito: características estas subidas en ADS + de 250 caracteres."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        # Enviar menos de 250 caracteres debe ser rechazado
        short_ads = "Texto corto de menos de doscientos cincuenta caracteres para pruebas."
        response = self.client.post('/api/v1/products/', {
            'title': 'Producto Test Corto',
            'price': 50000,
            'description': 'Descripción básica',
            'caracteristicas_ads': short_ads,
            'category': str(self.category.id)
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('caracteristicas_ads', str(response.content))

    def test_seller_creates_product_with_valid_ads_and_clean_url(self):
        """Requisito: Vendedor publica con ADS > 250 chars y genera URL limpia."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        response = self.client.post('/api/v1/products/', {
            'title': 'Teclado Mecánico Custom Pro RGB',
            'price': 89990,
            'description': 'Teclado para desarrolladores',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 10,
            'category': str(self.category.id),
            'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=900',
            'free_shipping': True,
            'installments': 6
        })
        self.assertEqual(response.status_code, 201)
        data = response.json().get('data', {})
        self.assertEqual(data.get('slug'), 'teclado-mecanico-custom-pro-rgb')

        # Buscar por URL limpia (slug)
        lookup_response = self.client.get('/api/v1/products/teclado-mecanico-custom-pro-rgb/')
        self.assertEqual(lookup_response.status_code, 200)
        lookup_data = lookup_response.json().get('data', {})
        self.assertEqual(lookup_data.get('title'), 'Teclado Mecánico Custom Pro RGB')
        # Verificar que expone el nombre del usuario que ingresó
        self.assertIsNotNone(lookup_data.get('seller_nombre'))
