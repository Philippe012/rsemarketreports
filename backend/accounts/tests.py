from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


class SignupTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post('/api/auth/signup/', {
            'email': 'new.user@example.com',
            'password': 'a-very-strong-pw-93',
            'password_confirm': 'a-very-strong-pw-93',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['email'], 'new.user@example.com')
        self.assertTrue(User.objects.filter(email='new.user@example.com').exists())

        # Session cookie is set: an authenticated-only endpoint now succeeds.
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['email'], 'new.user@example.com')

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(username='existing@example.com', email='existing@example.com', password='x')
        response = self.client.post('/api/auth/signup/', {
            'email': 'existing@example.com',
            'password': 'a-very-strong-pw-93',
            'password_confirm': 'a-very-strong-pw-93',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_signup_rejects_weak_password(self):
        response = self.client.post('/api/auth/signup/', {
            'email': 'weak@example.com',
            'password': '12345678',
            'password_confirm': '12345678',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.json())

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post('/api/auth/signup/', {
            'email': 'mismatch@example.com',
            'password': 'a-very-strong-pw-93',
            'password_confirm': 'something-else-42',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='person@example.com', email='person@example.com', password='correct-horse-99')

    def test_login_succeeds_with_correct_credentials(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'person@example.com',
            'password': 'correct-horse-99',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], 'person@example.com')

    def test_login_is_case_insensitive_on_email(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'PERSON@example.com',
            'password': 'correct-horse-99',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'person@example.com',
            'password': 'wrong-password',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_login_fails_for_unknown_email(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'nobody@example.com',
            'password': 'whatever',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_logout_clears_session(self):
        self.client.login(username='person@example.com', password='correct-horse-99')
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)

        logout_response = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_response.status_code, 204)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 403)


class MeViewTests(TestCase):
    def test_me_requires_authentication(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 403)


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pw@example.com', email='pw@example.com', password='original-pw-77')
        self.client.login(username='pw@example.com', password='original-pw-77')

    def test_change_password_succeeds_and_new_password_works(self):
        response = self.client.post('/api/auth/change-password/', {
            'current_password': 'original-pw-77',
            'new_password': 'brand-new-pw-88',
            'new_password_confirm': 'brand-new-pw-88',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 204)

        self.client.logout()
        login = self.client.post('/api/auth/login/', {
            'email': 'pw@example.com',
            'password': 'brand-new-pw-88',
        }, content_type='application/json')
        self.assertEqual(login.status_code, 200)

    def test_change_password_rejects_wrong_current_password(self):
        response = self.client.post('/api/auth/change-password/', {
            'current_password': 'not-the-real-one',
            'new_password': 'brand-new-pw-88',
            'new_password_confirm': 'brand-new-pw-88',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reset@example.com', email='reset@example.com', password='old-password-11')

    def test_request_always_returns_200_and_emails_known_users(self):
        response = self.client.post('/api/auth/password-reset/', {'email': 'reset@example.com'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('reset-password', mail.outbox[0].body)

    def test_request_for_unknown_email_still_returns_200_and_sends_nothing(self):
        response = self.client.post('/api/auth/password-reset/', {'email': 'nobody@example.com'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_with_valid_token_resets_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post('/api/auth/password-reset-confirm/', {
            'uid': uid,
            'token': token,
            'new_password': 'freshly-reset-55',
            'new_password_confirm': 'freshly-reset-55',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        login = self.client.post('/api/auth/login/', {
            'email': 'reset@example.com',
            'password': 'freshly-reset-55',
        }, content_type='application/json')
        self.assertEqual(login.status_code, 200)

    def test_confirm_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post('/api/auth/password-reset-confirm/', {
            'uid': uid,
            'token': 'not-a-real-token',
            'new_password': 'freshly-reset-55',
            'new_password_confirm': 'freshly-reset-55',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
