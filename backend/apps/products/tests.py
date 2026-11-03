from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import UserCredential
from apps.products.models import Category, Product
from apps.accounts.authentication import generate_jwt_token

class ProductRBACTests(TestCase):
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

    def test_anonymous_cannot_create_product(self):
        response = self.client.post('/api/v1/products/', {
            'title': 'Test Item',
            'price': 10000,
            'description': 'Desc',
            'category': str(self.category.id)
        })
        self.assertIn(response.status_code, [401, 403])

    def test_buyer_role_forbidden_to_create_product(self):
        """RBAC test: Comprador cannot publish products (ISO 27001 Access Restriction)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.buyer_token}')
        response = self.client.post('/api/v1/products/', {
            'title': 'Intento Comprador',
            'price': 15000,
            'description': 'Un comprador intentando publicar',
            'category': str(self.category.id)
        })
        self.assertEqual(response.status_code, 403)

    def test_seller_role_can_create_product(self):
        """RBAC test: Vendedor can publish products; product links only to AccountProxy."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        response = self.client.post('/api/v1/products/', {
            'title': 'Laptop Gamer RTX 4060',
            'price': 899990,
            'description': 'Laptop de alto rendimiento',
            'stock': 5,
            'category': str(self.category.id),
            'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=700',
            'free_shipping': True,
            'installments': 6
        })
        self.assertEqual(response.status_code, 201)
        data = response.json().get('data', {})
        self.assertEqual(data.get('title'), 'Laptop Gamer RTX 4060')

        # Verify database association: linked to seller's intermediate account
        product = Product.objects.get(title='Laptop Gamer RTX 4060')
        self.assertEqual(product.seller_account.id, self.seller.intermediate_account.id)
        # Verify response does NOT expose user's email or internal credential ID
        self.assertNotIn('email', str(response.content))

    def test_public_catalog_does_not_leak_seller_credentials(self):
        """ISO 27001 Data Leakage Prevention test."""
        Product.objects.create(
            title='Teclado Mecánico RGB',
            description='Switches red',
            price=49990,
            category=self.category,
            seller_account=self.seller.intermediate_account
        )
        response = self.client.get('/api/v1/products/')
        self.assertEqual(response.status_code, 200)
        content_str = response.content.decode('utf-8')
        # Ensure email is nowhere in public catalog response
        self.assertNotIn('vendedor_api@inacap.cl', content_str)
        # Ensure public alias IS present
        self.assertIn(self.seller.intermediate_account.public_alias, content_str)
