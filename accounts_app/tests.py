from django.test import TestCase
from django.urls import reverse


class AccountsUrlsTests(TestCase):
    def test_auth_routes_resolve(self):
        self.assertEqual(reverse('accounts_app:login'), '/auth/login/')
        self.assertEqual(reverse('accounts_app:register'), '/auth/register/')
        self.assertEqual(reverse('accounts_app:profile'), '/auth/profile/')
        self.assertEqual(reverse('accounts_app:password_reset'), '/auth/password-reset/')
