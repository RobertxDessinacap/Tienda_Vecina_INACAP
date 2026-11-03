from django.test import TestCase
from apps.accounts.models import UserCredential, UserProfile, Persona, Rol, UserRol

class AccountArchitectureTests(TestCase):
    """
    Verifica los requisitos del profesor:
    - Userdjango y el objeto Persona.
    - Entre el user y la persona debe ser el userprofile y este se puede mover en el sistema.
    - Roles: ROL -> UserRol para clientes y vendedores.
    """

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
