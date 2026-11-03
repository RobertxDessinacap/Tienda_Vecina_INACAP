from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import UserCredential
from apps.products.models import Category, Product

class PaymentAndCartTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Gadgets')
        self.seller = UserCredential.objects.create_user(
            email='vendedor_cart@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_SELLER
        )
        self.product1 = Product.objects.create(
            title='Mouse Inalámbrico Ergonómico',
            price=25000,
            stock=10,
            seller_profile=self.seller.user_profile,
            category=self.category,
            caracteristicas_ads='X' * 260,
            description='Mouse ergonómico'
        )
        self.product2 = Product.objects.create(
            title='Pad Mouse XXL Gamer',
            price=15000,
            stock=5,
            seller_profile=self.seller.user_profile,
            category=self.category,
            caracteristicas_ads='Y' * 260,
            description='Pad mouse extendido'
        )

    def test_safe_cart_calculation_anti_tampering(self):
        """
        Requisito: Los procesos donde tenga información delicada no deben estar generadas,
        calculadas o analizadas por JS.
        Verifica que el backend calcula el total exclusivamente desde los precios de la DB.
        """
        payload = {
            'items': [
                {'product_id': str(self.product1.id), 'quantity': 2},
                {'product_id': str(self.product2.id), 'quantity': 1, 'unit_price': 1} # JS intenta falsificar precio a 1 peso
            ]
        }
        response = self.client.post('/api/v1/payments/cart/calculate/', payload, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json().get('data', {})
        # Total esperado: (25000 * 2) + (15000 * 1) = 65000
        self.assertEqual(data.get('total'), 65000.0)

    def test_transbank_init_and_commit_flow(self):
        """Prueba de integración de flujo de pago Transbank Webpay Plus."""
        init_payload = {
            'items': [
                {'product_id': str(self.product1.id), 'quantity': 1}
            ],
            'payment_method': 'WEBPAY_PLUS'
        }
        init_response = self.client.post('/api/v1/payments/transbank/init/', init_payload, format='json')
        self.assertEqual(init_response.status_code, 201)
        init_data = init_response.json().get('data', {})
        self.assertIsNotNone(init_data.get('token'))
        self.assertIsNotNone(init_data.get('url'))

        # Confirmación (Commit)
        token = init_data.get('token')
        commit_response = self.client.post('/api/v1/payments/transbank/commit/', {'token': token}, format='json')
        self.assertEqual(commit_response.status_code, 200)
        voucher = commit_response.json().get('voucher', {})
        self.assertEqual(voucher.get('status'), 'APROBADO')
        self.assertIsNotNone(voucher.get('authorization_code'))
