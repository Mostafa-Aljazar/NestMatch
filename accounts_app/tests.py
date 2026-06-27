from django.test import TestCase
from django.urls import reverse

from .models import User


class AccountsUrlsTests(TestCase):
    def test_auth_routes_resolve(self):
        self.assertEqual(reverse('accounts_app:login'), '/auth/login/')
        self.assertEqual(reverse('accounts_app:register_page'), '/auth/register/')
        self.assertEqual(reverse('accounts_app:profile'), '/auth/profile/')


class AccountsProfileAjaxTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user({
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'date_of_birth': '1995-01-01',
            'gender': 'M',
            'country': 'egyptian',
        })
        self.client.force_login(self.user)

    def test_personal_info_update_returns_json_on_error(self):
        response = self.client.post(reverse('accounts_app:profile_update_personal_info'), {
            'first_name': 'A',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'test@example.com',
            'date_of_birth': '1995-01-01',
            'gender': 'M',
            'country': 'egyptian',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].split(';')[0], 'application/json')
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('first_name', data['errors'])
