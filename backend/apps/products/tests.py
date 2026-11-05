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

    def test_xss_payload_rejected_in_product_creation(self):
        """Seguridad OWASP Anti-XSS: Rechazar caracteres [ } * < > scripts en productos."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        response = self.client.post('/api/v1/products/', {
            'title': '<script>alert(1)</script> Teclado',
            'price': 50000,
            'description': 'Descripción con [}* caracteres maliciosos',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 5,
            'category': str(self.category.id)
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('anti-XSS', str(response.content))

    def test_search_endpoint_sanitizes_xss_and_brackets(self):
        """Seguridad: El parámetro de búsqueda q purga caracteres [ } * < > sin generar error."""
        response = self.client.get('/api/v1/products/?q=%5B%7D*%3Cscript%3E')
        self.assertEqual(response.status_code, 200)

    def test_seller_my_products_and_edit_delete_flow(self):
        """Verifica que el vendedor puede listar sus productos, editarlos y darlos de baja."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        # 1. Crear producto
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

        # 2. Listar mis productos (debe aparecer)
        my_res = self.client.get('/api/v1/products/my-products/')
        self.assertEqual(my_res.status_code, 200)
        slugs = [p['slug'] for p in my_res.json()['data']]
        self.assertIn(slug, slugs)

        # 3. Editar publicación
        edit_res = self.client.put(f'/api/v1/products/{slug}/', {
            'title': 'Monitor Gamer Curvo 27 Pro Edition',
            'price': 189990,
            'stock': 12,
            'description': 'Descripción actualizada',
            'caracteristicas_ads': self.valid_ads_text
        })
        self.assertEqual(edit_res.status_code, 200)
        new_slug = edit_res.json()['data']['slug']

        # 4. Dar de baja
        del_res = self.client.delete(f'/api/v1/products/{new_slug}/')
        self.assertEqual(del_res.status_code, 200)

        # 5. Confirmar eliminación
        lookup = self.client.get(f'/api/v1/products/{new_slug}/')
        self.assertEqual(lookup.status_code, 404)

    def test_new_product_has_no_default_rating_and_can_be_reviewed(self):
        """Verifica que los productos nuevos no tienen rating por defecto y los compradores pueden evaluarlos."""
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

        # El producto nuevo no debe tener rating predeterminado
        self.assertIsNone(prod_data.get('rating'))
        self.assertEqual(prod_data.get('reviews_count'), 0)

        # Un comprador evalúa el pedido
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.buyer_token}')
        review_res = self.client.post(f'/api/v1/products/{slug}/review/', {
            'rating': 5,
            'comment': 'Excelente compra, despacho súper rápido.'
        })
        self.assertEqual(review_res.status_code, 201)
        self.assertEqual(review_res.json()['data']['updated_rating'], 5.0)
        self.assertEqual(review_res.json()['data']['reviews_count'], 1)

    def test_register_official_store_and_exposure_in_product(self):
        """Verifica que el vendedor puede registrar su tienda oficial y se expone con URL en el producto."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.seller_token}')
        store_res = self.client.post('/api/v1/auth/register-store/', {
            'store_name': 'Inacap Store Oficial',
            'store_url': 'https://tiendaoficial.cl'
        })
        self.assertEqual(store_res.status_code, 200)
        self.assertTrue(store_res.json()['data']['is_official_store'])
        self.assertEqual(store_res.json()['data']['official_store_name'], 'Inacap Store Oficial')

        # Al consultar un producto del vendedor, se expone la tienda oficial y su URL
        create_res = self.client.post('/api/v1/products/', {
            'title': 'Notebook Pro Inacap',
            'price': 599990,
            'description': 'Laptop institucional',
            'caracteristicas_ads': self.valid_ads_text,
            'stock': 3,
            'category': str(self.category.id)
        })
        slug = create_res.json()['data']['slug']

        prod_res = self.client.get(f'/api/v1/products/{slug}/')
        self.assertEqual(prod_res.status_code, 200)
        data = prod_res.json()['data']
        self.assertTrue(data.get('is_official_store'))
        self.assertEqual(data.get('seller_official_store_name'), 'Inacap Store Oficial')
        self.assertEqual(data.get('seller_official_store_url'), 'https://tiendaoficial.cl')
