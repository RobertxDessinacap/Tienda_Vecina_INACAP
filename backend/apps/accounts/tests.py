from django.test import TestCase
from apps.accounts.models import UserCredential, AccountProxy

class AccountSecurityTests(TestCase):
    """Verifies ISO 27001 Intermediate Account isolation and RBAC."""

    def test_intermediate_account_automatically_created(self):
        user = UserCredential.objects.create_user(
            email='auditor@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_BUYER
        )
        self.assertIsNotNone(user.intermediate_account)
        self.assertIsInstance(user.intermediate_account, AccountProxy)
        self.assertTrue(user.intermediate_account.public_alias.startswith('auditor_'))
        # Ensure ID is not a predictable sequential integer
        self.assertEqual(len(str(user.intermediate_account.id)), 36)

    def test_seller_verification_flag(self):
        seller = UserCredential.objects.create_user(
            email='vendedor_test@inacap.cl',
            password='Password123!',
            role=UserCredential.ROLE_SELLER
        )
        self.assertTrue(seller.intermediate_account.is_verified_seller)
