from io import BytesIO
from unittest.mock import patch
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from apps.accounts.authentication import generate_jwt_token
from apps.accounts.models import UserCredential
from apps.payments.models import Order, OrderItem
from apps.products.models import Category, Product
from apps.products.utils import process_and_secure_product_image, MAX_FILE_SIZE_BYTES


class ProductProfRequirementsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Computación')

        self.admin = UserCredential.objects.create_user(
            email='admin_products_test@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_ADMIN
        )
        self.admin_token = generate_jwt_token(self.admin)

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

        self.other_buyer = UserCredential.objects.create_user(
            email='otro_comprador@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_BUYER
        )
        self.other_buyer_token = generate_jwt_token(self.other_buyer)

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
        self.assertIsNotNone(lookup_data.get('seller_nombre'))

    def test_xss_payload_rejected_in_product_creation(self):
        """Seguridad OWASP Anti-XSS: Rechazar etiquetas HTML, scripts anidados y URIs peligrosas."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        response = self.client.post('/api/v1/products/', {
            'title': '<script>alert(1)</script> Teclado',
            'price': 50000,
            'description': 'Descripción con <scr<script>ipt>alert(1)</script> malicioso',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 5,
            'category': str(self.category.id)
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('anti-XSS', str(response.content))

        # Payload anidado / URI / event handler sin etiquetas
        for bad_desc in ['<scr<script>ipt>alert(1)</script>', 'javascript:alert(1)', 'Ver detalle onerror=alert(1)']:
            res = self.client.post('/api/v1/products/', {
                'title': 'Producto Prueba XSS',
                'price': 50000,
                'description': bad_desc,
                'caracteristicas_ads': self.valid_ads_text,
                'stock': 5,
                'category': str(self.category.id)
            })
            self.assertEqual(res.status_code, 400)
            self.assertIn('anti-XSS', str(res.content))

    def test_commercial_punctuation_accepted_in_product_creation(self):
        """Usabilidad: Puntuación comercial ($ * [ ] ; ( ) % + - / : , .) debe aceptarse sin falsos positivos."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        response = self.client.post('/api/v1/products/', {
            'title': 'Monitor 24* [IPS] $199.990; oferta',
            'price': 199990,
            'description': 'Resolución 1920x1080 (Full HD) + 100% sRGB; garantía: 12 meses / envío rápido.',
            'caracteristicas_ads': self.valid_ads_text + " Incluye descuento 15% ($30.000) [Stock limitado]; HDMI/DP.",
            'stock': 8,
            'category': str(self.category.id)
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['data']['title'], 'Monitor 24* [IPS] $199.990; oferta')

    def test_search_endpoint_sanitizes_xss_and_brackets(self):
        """Seguridad: El parámetro de búsqueda q purga etiquetas/scripts sin generar error y soporta texto comercial."""
        response = self.client.get('/api/v1/products/?q=%5B%7D*%3Cscript%3E')
        self.assertEqual(response.status_code, 200)
        response_commercial = self.client.get('/api/v1/products/?q=%5BIPS%5D+%24199.990')
        self.assertEqual(response_commercial.status_code, 200)

    def test_seller_my_products_and_edit_delete_flow(self):
        """Verifica que el vendedor puede listar sus productos, editarlos y darlos de baja."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        create_res = self.client.post('/api/v1/products/', {
            'title': 'Monitor Gamer Curvo 27',
            'price': 199990,
            'description': 'Monitor para pruebas de edición',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 8,
            'category': str(self.category.id)
        })
        self.assertEqual(create_res.status_code, 201)
        slug = create_res.json()['data']['slug']

        my_res = self.client.get('/api/v1/products/my-products/')
        self.assertEqual(my_res.status_code, 200)
        slugs = [p['slug'] for p in my_res.json()['data']]
        self.assertIn(slug, slugs)

        edit_res = self.client.put(f'/api/v1/products/{slug}/', {
            'title': 'Monitor Gamer Curvo 27 Pro Edition',
            'price': 189990,
            'stock': 12,
            'description': 'Descripción actualizada',
            'caracteristicas_ads': self.valid_ads_text
        })
        self.assertEqual(edit_res.status_code, 200)
        new_slug = edit_res.json()['data']['slug']

        del_res = self.client.delete(f'/api/v1/products/{new_slug}/')
        self.assertEqual(del_res.status_code, 200)

        lookup = self.client.get(f'/api/v1/products/{new_slug}/')
        self.assertEqual(lookup.status_code, 404)

    def test_new_product_has_no_default_rating_and_can_be_reviewed(self):
        """Verifica rating nulo inicial, compra verificada obligatoria, bloqueo de auto-reseña y unicidad."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        create_res = self.client.post('/api/v1/products/', {
            'title': 'Smartband Fit Pulse 5',
            'price': 29990,
            'description': 'Banda inteligente para deporte',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 15,
            'category': str(self.category.id)
        })
        self.assertEqual(create_res.status_code, 201)
        prod_data = create_res.json()['data']
        slug = prod_data['slug']
        product = Product.objects.get(slug=slug)

        self.assertIsNone(prod_data.get('rating'))
        self.assertEqual(prod_data.get('reviews_count'), 0)

        # 1. Auto-reseña del vendedor rechazada (400)
        self_review_res = self.client.post(f'/api/v1/products/{slug}/review/', {
            'rating': 5,
            'comment': 'Excelente producto propio.'
        })
        self.assertEqual(self_review_res.status_code, 400)

        # 2. Comprador sin orden AUTHORIZED es rechazado (403)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_buyer_token}')
        unpurchased_res = self.client.post(f'/api/v1/products/{slug}/review/', {
            'rating': 1,
            'comment': 'Nunca lo compré pero opino igual.'
        })
        self.assertEqual(unpurchased_res.status_code, 403)

        # Comprador con orden INITIALIZED (no pagada) también recibe 403
        pending_order = Order.objects.create(
            buy_order='OC-PENDING1',
            buyer_profile=self.buyer.user_profile,
            total_amount=29990,
            status='INITIALIZED'
        )
        OrderItem.objects.create(
            order=pending_order,
            product=product,
            unit_price=29990,
            quantity=1,
            subtotal=29990
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.buyer_token}')
        unpaid_res = self.client.post(f'/api/v1/products/{slug}/review/', {
            'rating': 5,
            'comment': 'Orden no pagada.'
        })
        self.assertEqual(unpaid_res.status_code, 403)

        # 3. Comprador con orden AUTHORIZED sí puede evaluar (201)
        paid_order = Order.objects.create(
            buy_order='OC-AUTH001',
            buyer_profile=self.buyer.user_profile,
            total_amount=29990,
            status='AUTHORIZED'
        )
        OrderItem.objects.create(
            order=paid_order,
            product=product,
            unit_price=29990,
            quantity=1,
            subtotal=29990
        )
        review_res = self.client.post(f'/api/v1/products/{slug}/review/', {
            'rating': 5,
            'comment': 'Excelente compra, despacho súper rápido.'
        })
        self.assertEqual(review_res.status_code, 201)
        self.assertEqual(review_res.json()['data']['updated_rating'], 5.0)
        self.assertEqual(review_res.json()['data']['reviews_count'], 1)

        # 4. Reseña duplicada del mismo comprador rechazada (400)
        dup_res = self.client.post(f'/api/v1/products/{slug}/review/', {
            'rating': 4,
            'comment': 'Segunda reseña no permitida.'
        })
        self.assertEqual(dup_res.status_code, 400)

    def test_register_official_store_and_exposure_in_product(self):
        """
        Verifica moderación de Tienda Oficial:
        - Seller queda en PENDING con is_official_store=False
        - Admin aprueba -> is_official_store=True y producto la expone
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        store_res = self.client.post('/api/v1/auth/register-store/', {
            'store_name': 'Inacap Store Oficial',
            'store_url': 'https://tiendaoficial.cl'
        })
        self.assertEqual(store_res.status_code, 200)
        store_data = store_res.json()['data']
        self.assertEqual(store_data['official_store_status'], 'PENDING')
        self.assertFalse(store_data['is_official_store'])

        create_res = self.client.post('/api/v1/products/', {
            'title': 'Notebook Pro Inacap',
            'price': 599990,
            'description': 'Laptop institucional',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 3,
            'category': str(self.category.id)
        })
        self.assertEqual(create_res.status_code, 201)
        slug = create_res.json()['data']['slug']

        # Antes de aprobar, el producto no debe mostrar tienda oficial activa
        pending_prod_res = self.client.get(f'/api/v1/products/{slug}/')
        self.assertEqual(pending_prod_res.status_code, 200)
        self.assertFalse(pending_prod_res.json()['data']['is_official_store'])

        # Admin aprueba la tienda oficial
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        approve_res = self.client.post(
            f'/api/v1/auth/approve-store/{self.seller.user_profile.id}/',
            {'approved': True},
            format='json'
        )
        self.assertEqual(approve_res.status_code, 200)
        self.assertTrue(approve_res.json()['data']['is_official_store'])
        self.assertEqual(approve_res.json()['data']['official_store_status'], 'APPROVED')

        # Al consultar producto tras aprobación, expone tienda oficial y su URL
        prod_res = self.client.get(f'/api/v1/products/{slug}/')
        self.assertEqual(prod_res.status_code, 200)
        data = prod_res.json()['data']
        self.assertTrue(data.get('is_official_store'))
        self.assertEqual(data.get('seller_official_store_name'), 'Inacap Store Oficial')
        self.assertEqual(data.get('seller_official_store_url'), 'https://tiendaoficial.cl')
        self.assertEqual(data.get('seller_nombre'), 'Inacap Store Oficial')

    def test_non_official_seller_does_not_expose_persona_nombre_completo(self):
        """Privacidad PII (Gate 6): Producto de vendedor C2C no oficial expone public_alias y nunca Persona.nombre_completo."""
        persona = self.seller.user_profile.persona
        persona.nombres = 'Roberto Confidencial'
        persona.apellidos = 'Salazar Civil'
        persona.save()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        create_res = self.client.post('/api/v1/products/', {
            'title': 'Audífono C2C Privado',
            'price': 45000,
            'description': 'Producto de vendedor particular no oficial',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 4,
            'category': str(self.category.id)
        })
        self.assertEqual(create_res.status_code, 201)
        slug = create_res.json()['data']['slug']

        detail_res = self.client.get(f'/api/v1/products/{slug}/')
        self.assertEqual(detail_res.status_code, 200)
        data = detail_res.json()['data']
        self.assertEqual(data['seller_nombre'], self.seller.user_profile.public_alias)
        self.assertNotIn('Roberto Confidencial', str(detail_res.content))
        self.assertNotIn('Salazar Civil', str(detail_res.content))

    def test_existing_images_validation_rejects_malicious_schemes(self):
        """FINDING-14: Rechazar javascript:, data: y path traversal en existing_images; permitir /media/ y http/https."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        for bad_img in [
            ['javascript:alert(1)'],
            ['data:text/html,<script>alert(1)</script>'],
            ['/media/../etc/passwd'],
        ]:
            res = self.client.post('/api/v1/products/', {
                'title': 'Producto Imagen Insegura',
                'price': 39990,
                'description': 'Intento de inyección en galería',
                'caracteristicas_ads': self.valid_ads_text,
                'stock': 2,
                'category': str(self.category.id),
                'existing_images': bad_img,
            }, format='json')
            self.assertEqual(res.status_code, 400)

        ok_res = self.client.post('/api/v1/products/', {
            'title': 'Producto Imagen Segura',
            'price': 39990,
            'description': 'Galería con rutas válidas',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 2,
            'category': str(self.category.id),
            'existing_images': ['/media/productos/valid.jpg', 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=900'],
        }, format='json')
        self.assertEqual(ok_res.status_code, 201)

    def test_catalog_pagination_max_12_items_per_page(self):
        """FINDING-06: Paginación del catálogo público con máximo 12 ítems por página y metadatos completos."""
        for i in range(15):
            Product.objects.create(
                title=f'Producto Paginado {i:02d}',
                price=10000 + i * 100,
                stock=5,
                seller_profile=self.seller.user_profile,
                category=self.category,
                caracteristicas_ads=self.valid_ads_text,
                description='Descripción paginación'
            )

        res_p1 = self.client.get('/api/v1/products/')
        self.assertEqual(res_p1.status_code, 200)
        body1 = res_p1.json()
        self.assertEqual(body1['count'], 15)
        self.assertEqual(body1['page'], 1)
        self.assertEqual(body1['total_pages'], 2)
        self.assertIsNotNone(body1['next'])
        self.assertIsNone(body1['previous'])
        self.assertEqual(len(body1['data']), 12)

        res_p2 = self.client.get('/api/v1/products/?page=2')
        self.assertEqual(res_p2.status_code, 200)
        body2 = res_p2.json()
        self.assertEqual(body2['count'], 15)
        self.assertEqual(body2['page'], 2)
        self.assertEqual(body2['total_pages'], 2)
        self.assertIsNone(body2['next'])
        self.assertIsNotNone(body2['previous'])
        self.assertEqual(len(body2['data']), 3)

    def test_image_utils_guards_and_normalization(self):
        """Verifica guarda de tamaño bruto (<=10MB), magic bytes y normalización 900x600 <= 1MB."""
        buf = BytesIO()
        Image.new('RGB', (1200, 800), (20, 120, 220)).save(buf, format='PNG')
        buf.seek(0)
        valid_file = SimpleUploadedFile('test.png', buf.read(), content_type='image/png')
        processed = process_and_secure_product_image(valid_file)
        self.assertLessEqual(processed.size, MAX_FILE_SIZE_BYTES)
        out_img = Image.open(processed)
        self.assertEqual(out_img.size, (900, 600))

        fake_file = SimpleUploadedFile('evil.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
        with self.assertRaises(ValidationError):
            process_and_secure_product_image(fake_file)

        with patch('apps.products.utils.MAX_UPLOAD_BYTES', 100):
            buf.seek(0)
            oversized = SimpleUploadedFile('big.png', buf.read(), content_type='image/png')
            with self.assertRaises(ValidationError):
                process_and_secure_product_image(oversized)

    @override_settings(DEBUG=False)
    def test_seed_ecommerce_refuses_without_env_passwords_in_production(self):
        """SEC-FE-02 / Gate 2: seed_ecommerce falla cerrado si DEBUG=False sin variables SEED_*_PASSWORD."""
        with patch.dict('os.environ', {'SEED_ADMIN_PASSWORD': '', 'SEED_SELLER_PASSWORD': '', 'SEED_BUYER_PASSWORD': ''}):
            with self.assertRaises(CommandError):
                call_command('seed_ecommerce')
