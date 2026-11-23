from datetime import timedelta
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.authentication import generate_jwt_token
from apps.accounts.models import Persona, RevokedToken, Rol, UserCredential, UserProfile, UserRol
from apps.accounts.permissions import IsSellerOrAdmin
from apps.accounts.serializers import UserProfilePrivateSerializer, UserProfileSerializer
from apps.security.middleware import SecurityAuditLoggingMiddleware


class AccountArchitectureTests(TestCase):
    """
    Verifica los requisitos del profesor y controles de seguridad ISO 27001:
    - Userdjango y el objeto Persona.
    - Entre el user y la persona debe ser el userprofile y este se puede mover en el sistema.
    - Roles: ROL -> UserRol para clientes y vendedores.
    - Controles de autenticación, RBAC, rate limiting, revocación JWT y moderación.
    """

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def tearDown(self):
        cache.clear()

    def test_user_profile_between_user_and_persona(self):
        user = UserCredential.objects.create_user(
            email='estudiante@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_BUYER
        )
        # 1. Comprobar que existe el UserProfile
        self.assertIsNotNone(user.user_profile)
        self.assertIsInstance(user.user_profile, UserProfile)

        # 2. Comprobar que el UserProfile conecta con el objeto Persona
        persona = user.user_profile.persona
        self.assertIsNotNone(persona)
        self.assertIsInstance(persona, Persona)
        self.assertEqual(persona.correo_contacto, 'estudiante@inacap.cl')

        # 3. Comprobar que el UserProfile tiene su asignación ROL -> UserRol
        user_roles = user.user_profile.user_roles.all()
        self.assertEqual(user_roles.count(), 1)
        self.assertEqual(user_roles.first().rol.codigo, 'BUYER')

    def test_seller_role_assignment(self):
        seller = UserCredential.objects.create_user(
            email='vendedor_test@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_SELLER
        )
        self.assertTrue(seller.user_profile.is_verified_seller)
        self.assertTrue(seller.user_profile.has_role('SELLER'))

    def test_upgrade_buyer_to_seller(self):
        user = UserCredential.objects.create_user(
            email='comprador_ascenso@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_BUYER
        )
        self.client.force_authenticate(user=user)

        response = self.client.post('/api/v1/auth/upgrade-seller/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')

        user.refresh_from_db()
        self.assertEqual(user.role, UserCredential.ROLE_SELLER)
        self.assertTrue(user.user_profile.is_verified_seller)
        self.assertTrue(user.user_profile.has_role('SELLER'))

    def test_admin_privilege_preserved_on_upgrade_seller(self):
        admin = UserCredential.objects.create_superuser(
            email='admin_upgrade@inacap.cl',
            password='Password123!'
        )
        self.client.force_authenticate(user=admin)

        response = self.client.post('/api/v1/auth/upgrade-seller/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], UserCredential.ROLE_ADMIN)
        self.assertIn('persona_nombre', response.data['user']['user_profile'])

        admin.refresh_from_db()
        self.assertEqual(admin.role, UserCredential.ROLE_ADMIN)
        self.assertTrue(admin.user_profile.has_role('ADMIN'))

    def test_user_rol_sync_and_is_seller_or_admin_denial_on_demotion(self):
        seller = UserCredential.objects.create_user(
            email='demoted_seller@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_SELLER
        )
        self.assertTrue(seller.user_profile.has_role('SELLER'))

        factory = RequestFactory()
        perm = IsSellerOrAdmin()
        req = factory.post('/api/v1/auth/register-store/')
        req.user = seller
        self.assertTrue(perm.has_permission(req, None))

        # Degradar a BUYER debe sincronizar UserRol y revocar permiso IsSellerOrAdmin
        seller.role = UserCredential.ROLE_BUYER
        seller.save()
        seller.refresh_from_db()

        self.assertFalse(seller.user_profile.has_role('SELLER'))
        self.assertTrue(seller.user_profile.has_role('BUYER'))
        self.assertFalse(perm.has_permission(req, None))

        self.client.force_authenticate(user=seller)
        res = self.client.post('/api/v1/auth/register-store/', {
            'store_name': 'Tienda Degradada',
            'store_url': 'https://tiendadegradada.cl'
        }, format='json')
        self.assertEqual(res.status_code, 403)

    def test_login_and_register_rate_limiting(self):
        # Register throttle: 3/minute
        for idx in range(3):
            res = self.client.post('/api/v1/auth/register/', {
                'email': f'throttle_reg_{idx}@inacap.cl',
                'password': 'StrongPassword123!',
                'full_name': 'Usuario Prueba',
            }, format='json')
            self.assertNotEqual(res.status_code, 429)

        throttled_reg = self.client.post('/api/v1/auth/register/', {
            'email': 'throttle_reg_blocked@inacap.cl',
            'password': 'StrongPassword123!',
            'full_name': 'Usuario Bloqueado',
        }, format='json')
        self.assertEqual(throttled_reg.status_code, 429)

        cache.clear()

        # Login throttle: 5/minute
        UserCredential.objects.create_user(
            email='throttle_login@inacap.cl',
            password='StrongPassword123!',
            role=UserCredential.ROLE_BUYER
        )
        for _ in range(5):
            res = self.client.post('/api/v1/auth/login/', {
                'email': 'throttle_login@inacap.cl',
                'password': 'WrongPassword123!',
            }, format='json')
            self.assertNotEqual(res.status_code, 429)

        throttled_login = self.client.post('/api/v1/auth/login/', {
            'email': 'throttle_login@inacap.cl',
            'password': 'WrongPassword123!',
        }, format='json')
        self.assertEqual(throttled_login.status_code, 429)

    def test_duplicate_rut_returns_400_with_no_orphan_user(self):
        res1 = self.client.post('/api/v1/auth/register/', {
            'email': 'rut1@inacap.cl',
            'password': 'StrongPassword123!',
            'full_name': 'Titular Uno',
            'rut': '12.345.678-k',
        }, format='json')
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post('/api/v1/auth/register/', {
            'email': 'rut2@inacap.cl',
            'password': 'StrongPassword123!',
            'full_name': 'Titular Dos',
            'rut': '12.345.678-K',
        }, format='json')
        self.assertEqual(res2.status_code, 400)
        self.assertFalse(UserCredential.objects.filter(email='rut2@inacap.cl').exists())

    def test_registration_text_validation_allows_punctuation_and_blocks_scripts(self):
        ok_res = self.client.post('/api/v1/auth/register/', {
            'email': 'punct_ok@inacap.cl',
            'password': 'StrongPassword123!',
            'full_name': "María-José O'Connor",
            'custom_alias': 'Café & Té (Norte)',
        }, format='json')
        self.assertEqual(ok_res.status_code, 201)

        bad_res = self.client.post('/api/v1/auth/register/', {
            'email': 'xss_bad@inacap.cl',
            'password': 'StrongPassword123!',
            'full_name': 'Normal Name',
            'custom_alias': '<script>alert(1)</script>',
        }, format='json')
        self.assertEqual(bad_res.status_code, 400)

    def test_locked_user_jwt_rejected(self):
        user = UserCredential.objects.create_user(
            email='locked_jwt@inacap.cl',
            password='StrongPassword123!',
            role=UserCredential.ROLE_BUYER
        )
        token = generate_jwt_token(user)

        user.locked_until = timezone.now() + timedelta(minutes=15)
        user.save(update_fields=['locked_until'])

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get('/api/v1/auth/me/')
        self.assertEqual(res.status_code, 401)

    def test_jwt_logout_revocation(self):
        user = UserCredential.objects.create_user(
            email='logout_jwt@inacap.cl',
            password='StrongPassword123!',
            role=UserCredential.ROLE_BUYER
        )
        token = generate_jwt_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        me_before = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_before.status_code, 200)

        logout_res = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(logout_res.status_code, 200)
        self.assertEqual(RevokedToken.objects.filter(user=user).count(), 1)

        me_after = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_after.status_code, 401)

    def test_official_store_moderation_and_https_validation(self):
        seller = UserCredential.objects.create_user(
            email='store_seller@inacap.cl',
            password='StrongPassword123!',
            role=UserCredential.ROLE_SELLER
        )
        admin = UserCredential.objects.create_superuser(
            email='store_admin@inacap.cl',
            password='StrongPassword123!'
        )
        seller_token = generate_jwt_token(seller)
        admin_token = generate_jwt_token(admin)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {seller_token}')

        # HTTP no seguro rechazado
        http_res = self.client.post('/api/v1/auth/register-store/', {
            'store_name': 'Tienda Insegura',
            'store_url': 'http://tiendainsegura.cl',
        }, format='json')
        self.assertEqual(http_res.status_code, 400)

        # javascript: rechazado
        js_res = self.client.post('/api/v1/auth/register-store/', {
            'store_name': 'Tienda JS',
            'store_url': 'javascript:alert(1)',
        }, format='json')
        self.assertEqual(js_res.status_code, 400)

        # Registro válido por SELLER queda PENDING e is_official_store=False
        reg_res = self.client.post('/api/v1/auth/register-store/', {
            'store_name': 'Tienda Vecina Oficial',
            'store_url': 'https://tiendavecina.cl',
        }, format='json')
        self.assertEqual(reg_res.status_code, 200)
        self.assertFalse(reg_res.data['data']['is_official_store'])
        self.assertEqual(reg_res.data['data']['official_store_status'], UserProfile.STORE_STATUS_PENDING)

        profile_id = seller.user_profile.id

        # Non-admin no puede aprobar
        forbidden_res = self.client.post(f'/api/v1/auth/approve-store/{profile_id}/', {
            'approved': True,
        }, format='json')
        self.assertEqual(forbidden_res.status_code, 403)

        # Admin aprueba la tienda
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        approve_res = self.client.post(f'/api/v1/auth/approve-store/{profile_id}/', {
            'approved': True,
        }, format='json')
        self.assertEqual(approve_res.status_code, 200)
        self.assertTrue(approve_res.data['data']['is_official_store'])
        self.assertEqual(approve_res.data['data']['official_store_status'], UserProfile.STORE_STATUS_APPROVED)

        # Admin puede rechazar
        reject_res = self.client.post(f'/api/v1/auth/approve-store/{profile_id}/', {
            'approved': False,
        }, format='json')
        self.assertEqual(reject_res.status_code, 200)
        self.assertFalse(reject_res.data['data']['is_official_store'])
        self.assertEqual(reject_res.data['data']['official_store_status'], UserProfile.STORE_STATUS_REJECTED)

        # Admin registrando su propia tienda obtiene aprobación inmediata
        admin_store_res = self.client.post('/api/v1/auth/register-store/', {
            'store_name': 'Tienda Oficial Admin',
            'store_url': 'https://adminstore.cl',
        }, format='json')
        self.assertEqual(admin_store_res.status_code, 200)
        self.assertTrue(admin_store_res.data['data']['is_official_store'])
        self.assertEqual(admin_store_res.data['data']['official_store_status'], UserProfile.STORE_STATUS_APPROVED)

    def test_public_vs_private_profile_serializer_fields(self):
        user = UserCredential.objects.create_user(
            email='pii_check@inacap.cl',
            password='StrongPassword123!',
            role=UserCredential.ROLE_BUYER
        )
        public_data = UserProfileSerializer(user.user_profile).data
        private_data = UserProfilePrivateSerializer(user.user_profile).data

        self.assertNotIn('persona_nombre', public_data)
        self.assertIn('official_store_status', public_data)
        self.assertIn('persona_nombre', private_data)

    @override_settings(DEBUG=False, TRUST_X_FORWARDED_FOR=True)
    def test_security_headers_and_crlf_log_sanitization(self):
        res = self.client.get('/api/v1/auth/me/', secure=True)
        self.assertEqual(res['Permissions-Policy'], 'geolocation=(self), microphone=(), camera=()')
        self.assertEqual(res['Strict-Transport-Security'], 'max-age=31536000; includeSubDomains')

        csp = res['Content-Security-Policy']
        directives = {}
        for part in csp.split(';'):
            tokens = part.strip().split()
            if tokens:
                directives[tokens[0]] = tokens[1:]

        self.assertNotIn('https:', directives.get('connect-src', []))
        self.assertNotIn('https:', directives.get('img-src', []))
        self.assertNotIn('https:', directives.get('font-src', []))
        self.assertIn('https://webpay3gint.transbank.cl', directives.get('connect-src', []))
        self.assertIn('https://webpay3gint.transbank.cl', directives.get('form-action', []))

        with self.assertLogs('security.audit', level='INFO') as cm:
            self.client.post(
                '/api/v1/auth/login/',
                {'email': 'none@inacap.cl', 'password': 'bad'},
                format='json',
                HTTP_X_FORWARDED_FOR='1.2.3.4\r\n[AUDIT] FORGED_LINE',
                secure=True,
            )
        joined_logs = '\n'.join(cm.output)
        self.assertNotIn('FORGED_LINE', joined_logs)
        self.assertIn('IP: Invalid_IP', joined_logs)

        rf = RequestFactory()
        mw = SecurityAuditLoggingMiddleware(lambda req: HttpResponse('ok'))
        injected_req = rf.post('/api/v1/auth/login/')
        injected_req.path = '/api/v1/auth/login/\r\n[AUDIT] INJECTED_PATH'
        injected_req.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.9, 10.0.0.1'
        with self.assertLogs('security.audit', level='INFO') as cm_path:
            mw(injected_req)
        self.assertEqual(len(cm_path.output), 1)
        self.assertNotIn('\n', cm_path.output[0])
        self.assertNotIn('\r', cm_path.output[0])
        self.assertIn('IP: 203.0.113.9', cm_path.output[0])
