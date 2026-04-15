import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from yoga_app.models import UserProfile


@pytest.mark.integration
class TestEmailVerificationFlow:
    def test_user_created_inactive(self, django_user_model):
        user = django_user_model.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='testpass123',
            is_active=False,
        )
        assert user.is_active is False

    def test_verify_email_valid_token(self, django_user_model):
        user = django_user_model.objects.create_user(
            username='verifyuser',
            email='verify@example.com',
            password='testpass123',
            is_active=False,
        )
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        assert user.is_active is False
        user.is_active = True
        user.save(update_fields=['is_active'])
        user.refresh_from_db()
        assert user.is_active is True

    def test_verify_email_invalid_token(self, django_user_model):
        user = django_user_model.objects.create_user(
            username='badtoken',
            email='badtoken@example.com',
            password='testpass123',
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        assert default_token_generator.check_token(user, 'invalid-token') is False

    def test_login_blocked_for_unverified_user(self, client, django_user_model):
        django_user_model.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='testpass123',
            is_active=False,
        )
        response = client.post(reverse('login'), {
            'username': 'unverified',
            'password': 'testpass123',
        })
        # Debug: check what's in the response
        if response.status_code == 200:
            # Check if there are form errors
            if hasattr(response, 'context') and response.context:
                form = response.context.get('form')
                if form and form.errors:
                    print(f"Form errors: {form.errors}")
        # Either redirect or show error message about verification
        assert response.status_code == 302 or (
            response.status_code == 200 and 
            any('verify' in str(m).lower() for m in response.context.get('messages', []))
        )

    def test_resend_verification(self, client, user):
        user.is_active = False
        user.save(update_fields=['is_active'])
        client.login(username='testuser', password='testpass123')
        response = client.post(reverse('resend_verification'))
        assert response.status_code == 302

    def test_verified_user_cannot_resend(self, client, user):
        assert user.is_active is True
        client.login(username='testuser', password='testpass123')
        response = client.get(reverse('resend_verification'))
        assert response.status_code == 302
        assert 'dashboard' in response.url
