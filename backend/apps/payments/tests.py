from unittest.mock import patch
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from apps.accounts.models import UserCredential
from apps.payments.models import Order, OrderItem
from apps.payments.services import TransbankWebpayService
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
                {'product_id': str(self.product2.id), 'quantity': 1, 'unit_price': 1}
            ]
        }
        response = self.client.post('/api/v1/payments/cart/calculate/', payload, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json().get('data', {})
        # Total esperado: (25000 * 2) + (15000 * 1) = 65000
        self.assertEqual(data.get('total'), 65000.0)

    @patch('apps.payments.services.Transaction')
    def test_transbank_init_and_commit_flow(self, mock_tx_cls):
        """Prueba de integración de flujo de pago Transbank Webpay Plus con SDK mockeado."""
        mock_tx = mock_tx_cls.return_value
        mock_tx.create.return_value = {
            'token': '01ab12cd34ef567890abcdef1234567890abcdef1234567890abcdef12345678',
            'url': 'https://webpay3gint.transbank.cl/webpayserver/initTransaction',
        }
        mock_tx.commit.return_value = {
            'response_code': 0,
            'authorization_code': '1213',
            'amount': 25000,
            'card_detail': {'card_number': '6623'},
            'payment_type_code': 'VN',
            'shares_number': 1,
        }

        init_payload = {
            'items': [
                {'product_id': str(self.product1.id), 'quantity': 1}
            ],
            'payment_method': 'WEBPAY_PLUS'
        }
        init_response = self.client.post('/api/v1/payments/transbank/init/', init_payload, format='json')
        self.assertEqual(init_response.status_code, 201)
        init_data = init_response.json().get('data', {})
        self.assertEqual(init_data.get('token'), '01ab12cd34ef567890abcdef1234567890abcdef1234567890abcdef12345678')
        self.assertIsNotNone(init_data.get('url'))

        # Confirmación (Commit)
        token = init_data.get('token')
        commit_response = self.client.post('/api/v1/payments/transbank/commit/', {'token': token}, format='json')
        self.assertEqual(commit_response.status_code, 200)
        voucher = commit_response.json().get('voucher', {})
        self.assertEqual(voucher.get('status'), 'APROBADO')
        self.assertEqual(voucher.get('authorization_code'), '1213')

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 9)
        order = Order.objects.get(transbank_token=token)
        self.assertEqual(order.status, 'AUTHORIZED')

    @patch('apps.payments.services.Transaction')
    def test_transbank_init_fail_closed_on_sdk_error(self, mock_tx_cls):
        """Fail-closed: Si Transbank create falla, init retorna 502 y no genera token simulado ni orden."""
        mock_tx = mock_tx_cls.return_value
        mock_tx.create.side_effect = Exception("Transbank 503 Unavailable")

        init_response = self.client.post('/api/v1/payments/transbank/init/', {
            'items': [{'product_id': str(self.product1.id), 'quantity': 1}],
            'payment_method': 'WEBPAY_PLUS'
        }, format='json')
        self.assertEqual(init_response.status_code, 502)
        self.assertEqual(Order.objects.count(), 0)

    @patch('apps.payments.services.Transaction')
    def test_transbank_commit_fail_closed_on_exception(self, mock_tx_cls):
        """FINDING-01: Excepción en tx.commit debe marcar FAILED, retornar 400 y no descontar stock."""
        order = Order.objects.create(
            buy_order='OC-EXC-001',
            total_amount=25000,
            status='INITIALIZED',
            transbank_token='real_tbk_token_exc_001'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            unit_price=25000,
            quantity=2,
            subtotal=50000
        )
        mock_tx_cls.return_value.commit.side_effect = Exception("Timeout de pasarela")

        res = self.client.post('/api/v1/payments/transbank/commit/', {'token': 'real_tbk_token_exc_001'}, format='json')
        self.assertEqual(res.status_code, 400)

        order.refresh_from_db()
        self.product1.refresh_from_db()
        self.assertEqual(order.status, 'FAILED')
        self.assertEqual(self.product1.stock, 10)

    @patch('apps.payments.services.Transaction')
    def test_transbank_commit_fail_closed_on_non_zero_response_code(self, mock_tx_cls):
        """FINDING-01: response_code != 0 debe marcar FAILED, retornar 400 y no descontar stock."""
        order = Order.objects.create(
            buy_order='OC-REJ-001',
            total_amount=25000,
            status='INITIALIZED',
            transbank_token='real_tbk_token_rej_001'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            unit_price=25000,
            quantity=1,
            subtotal=25000
        )
        mock_tx_cls.return_value.commit.return_value = {
            'response_code': -1,
            'amount': 25000,
        }

        res = self.client.post('/api/v1/payments/transbank/commit/', {'token': 'real_tbk_token_rej_001'}, format='json')
        self.assertEqual(res.status_code, 400)

        order.refresh_from_db()
        self.product1.refresh_from_db()
        self.assertEqual(order.status, 'FAILED')
        self.assertEqual(self.product1.stock, 10)

    @patch('apps.payments.services.Transaction')
    def test_transbank_commit_rejects_simulated_tbk_token(self, mock_tx_cls):
        """FINDING-01: Tokens falsos con prefijo tbk_token_* son rechazados fail-closed."""
        order = Order.objects.create(
            buy_order='OC-FAKE-001',
            total_amount=25000,
            status='INITIALIZED',
            transbank_token='tbk_token_simulated_bypass'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            unit_price=25000,
            quantity=1,
            subtotal=25000
        )

        res = self.client.post('/api/v1/payments/transbank/commit/', {'token': 'tbk_token_simulated_bypass'}, format='json')
        self.assertEqual(res.status_code, 400)
        mock_tx_cls.return_value.commit.assert_not_called()

        order.refresh_from_db()
        self.product1.refresh_from_db()
        self.assertEqual(order.status, 'FAILED')
        self.assertEqual(self.product1.stock, 10)

    @patch('apps.payments.services.Transaction')
    def test_transbank_commit_replay_attack_blocked(self, mock_tx_cls):
        """FINDING-02: Segundo commit con el mismo token retorna 400 y NO vuelve a descontar stock ni llamar a Transbank."""
        mock_tx = mock_tx_cls.return_value
        mock_tx.create.return_value = {
            'token': 'valid_tbk_replay_token_001',
            'url': 'https://webpay3gint.transbank.cl/webpayserver/initTransaction',
        }
        mock_tx.commit.return_value = {
            'response_code': 0,
            'authorization_code': 'AUTH777',
            'amount': 50000,
            'card_detail': {'card_number': '6623'},
            'payment_type_code': 'VN',
            'shares_number': 1,
        }

        init_res = self.client.post('/api/v1/payments/transbank/init/', {
            'items': [{'product_id': str(self.product1.id), 'quantity': 2}],
            'payment_method': 'WEBPAY_PLUS'
        }, format='json')
        self.assertEqual(init_res.status_code, 201)
        token = init_res.json()['data']['token']

        first_commit = self.client.post('/api/v1/payments/transbank/commit/', {'token': token}, format='json')
        self.assertEqual(first_commit.status_code, 200)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 8)

        # Ataque de repetición (Replay)
        second_commit = self.client.post('/api/v1/payments/transbank/commit/', {'token': token}, format='json')
        self.assertEqual(second_commit.status_code, 400)
        self.assertEqual(mock_tx.commit.call_count, 1)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 8)

    @patch('apps.payments.services.Transaction')
    def test_transbank_commit_insufficient_stock_refunds_and_returns_409(self, mock_tx_cls):
        """FINDING-03: Si el stock se agotó al momento de confirmar, ejecuta refund, marca REVERSED y retorna 409."""
        mock_tx = mock_tx_cls.return_value
        mock_tx.create.return_value = {
            'token': 'valid_tbk_race_token_001',
            'url': 'https://webpay3gint.transbank.cl/webpayserver/initTransaction',
        }
        mock_tx.commit.return_value = {
            'response_code': 0,
            'authorization_code': 'AUTH999',
            'amount': 60000,
            'card_detail': {'card_number': '6623'},
            'payment_type_code': 'VN',
            'shares_number': 1,
        }
        mock_tx.refund.return_value = {
            'type': 'REVERSED',
            'response_code': 0,
        }

        init_res = self.client.post('/api/v1/payments/transbank/init/', {
            'items': [{'product_id': str(self.product2.id), 'quantity': 4}],
            'payment_method': 'WEBPAY_PLUS'
        }, format='json')
        self.assertEqual(init_res.status_code, 201)
        token = init_res.json()['data']['token']

        # Otro comprador consume stock antes del commit
        self.product2.stock = 2
        self.product2.save(update_fields=['stock'])

        commit_res = self.client.post('/api/v1/payments/transbank/commit/', {'token': token}, format='json')
        self.assertEqual(commit_res.status_code, 409)
        mock_tx.refund.assert_called_once_with(token, 60000)

        order = Order.objects.get(transbank_token=token)
        self.product2.refresh_from_db()
        self.assertEqual(order.status, 'REVERSED')
        self.assertEqual(self.product2.stock, 2)

    def test_malformed_cart_quantities_and_duplicate_stock_return_400(self):
        """FINDING-13: Entradas inválidas en carrito retornan HTTP 400 fail (nunca 500) y agregan cantidades duplicadas."""
        invalid_payloads = [
            {'items': [{'product_id': str(self.product1.id), 'quantity': 'invalid'}]},
            {'items': [{'product_id': str(self.product1.id), 'quantity': None}]},
            {'items': [{'product_id': str(self.product1.id), 'quantity': True}]},
            {'items': [{'product_id': str(self.product1.id), 'quantity': -1}]},
            {'items': [{'product_id': str(self.product1.id), 'quantity': 0}]},
            {'items': [{'product_id': str(self.product1.id), 'quantity': 1.5}]},
            {'items': [{'product_id': 'not-a-uuid', 'quantity': 1}]},
            {'items': ['bad-item-not-a-dict']},
            {'items': []},
            # Entradas duplicadas del mismo product2 cuya suma (3 + 3 = 6) excede stock=5
            {'items': [
                {'product_id': str(self.product2.id), 'quantity': 3},
                {'product_id': str(self.product2.id), 'quantity': 3},
            ]},
        ]
        for payload in invalid_payloads:
            res_calc = self.client.post('/api/v1/payments/cart/calculate/', payload, format='json')
            self.assertEqual(res_calc.status_code, 400, f"Falló calculate con payload: {payload}")
            self.assertEqual(res_calc.json().get('status'), 'fail')

            res_init = self.client.post('/api/v1/payments/transbank/init/', payload, format='json')
            self.assertEqual(res_init.status_code, 400, f"Falló init con payload: {payload}")
            self.assertEqual(res_init.json().get('status'), 'fail')

    @override_settings(FRONTEND_URL='http://localhost:5173')
    @patch('apps.payments.services.Transaction')
    def test_transbank_browser_get_redirect_and_aborted_flow(self, mock_tx_cls):
        """Verifica retorno GET de Transbank (aprobado -> 302 AUTHORIZED y TBK_TOKEN abortado -> 302 CANCELLED)."""
        mock_tx = mock_tx_cls.return_value
        mock_tx.commit.return_value = {
            'response_code': 0,
            'authorization_code': 'AUTH_GET',
            'amount': 25000,
            'card_detail': {'card_number': '6623'},
            'payment_type_code': 'VN',
            'shares_number': 1,
        }

        order_ok = Order.objects.create(
            buy_order='OC-GET-OK',
            total_amount=25000,
            status='INITIALIZED',
            transbank_token='real_tbk_get_ok'
        )
        OrderItem.objects.create(
            order=order_ok,
            product=self.product1,
            unit_price=25000,
            quantity=1,
            subtotal=25000
        )

        get_ok = self.client.get('/api/v1/payments/transbank/commit/?token_ws=real_tbk_get_ok')
        self.assertEqual(get_ok.status_code, 302)
        self.assertIn('payment_status=AUTHORIZED', get_ok['Location'])
        self.assertIn('buy_order=OC-GET-OK', get_ok['Location'])

        order_abort = Order.objects.create(
            buy_order='OC-GET-ABORT',
            total_amount=25000,
            status='INITIALIZED',
            transbank_token='real_tbk_get_abort'
        )
        get_abort = self.client.get('/api/v1/payments/transbank/commit/?TBK_TOKEN=real_tbk_get_abort')
        self.assertEqual(get_abort.status_code, 302)
        self.assertIn('payment_status=CANCELLED', get_abort['Location'])
        order_abort.refresh_from_db()
        self.assertEqual(order_abort.status, 'FAILED')

    @override_settings(TRANSBANK_ENVIRONMENT='LIVE')
    def test_transbank_service_supports_live_environment(self):
        """Verifica que get_tx() selecciona IntegrationType.LIVE cuando TRANSBANK_ENVIRONMENT='LIVE'."""
        from transbank.common.integration_type import IntegrationType
        tx = TransbankWebpayService().get_tx()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.options.integration_type, IntegrationType.LIVE)
