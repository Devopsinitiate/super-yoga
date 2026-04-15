import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from yoga_app.forms import (
    UserRegisterForm,
    UserLoginForm,
    UserAccountUpdateForm,
    UserProfileForm,
    CustomPasswordChangeForm,
)
from yoga_app.models import UserProfile
from yoga_app.services import EnrollmentService

logger = logging.getLogger(__name__)


def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_url = f"{request.scheme}://{request.get_host()}/verify-email/{uid}/{token}/"

    subject = "Verify Your Email - Yoga Kailasa"
    message = f"""
Hello {user.username},

Thank you for registering with Yoga Kailasa! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 3 days.

If you did not create an account, please ignore this email.

Namaste,
The Yoga Kailasa Team
"""
    html_message = f"""
<html>
<body style="font-family: 'Manrope', sans-serif; background-color: #fff8f3; padding: 40px;">
    <div style="max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 4px 16px rgba(0,0,0,0.08);">
        <h1 style="font-family: 'Noto Serif', serif; color: #855300; margin-bottom: 16px;">Welcome to Yoga Kailasa</h1>
        <p style="color: #534434; line-height: 1.6;">Hello <strong>{user.username}</strong>,</p>
        <p style="color: #534434; line-height: 1.6;">Thank you for joining our community! Please verify your email address to complete your registration.</p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="{verification_url}" style="background: linear-gradient(135deg, #855300, #f59e0b); color: white; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; display: inline-block;">Verify Email</a>
        </div>
        <p style="color: #534434; font-size: 14px;">This link expires in 3 days. If you didn't create an account, you can safely ignore this email.</p>
        <p style="color: #855300; font-family: 'Noto Serif', serif; margin-top: 24px;">Namaste,<br>The Yoga Kailasa Team</p>
    </div>
</body>
</html>
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class CustomLoginView(LoginView):
    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, 'Please verify your email address before logging in. Check your inbox for the verification link.')
            return redirect('verify_email_pending', user_id=user.pk)
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {user.username}! You have logged in successfully.")
        return response

    def form_invalid(self, form):
        error_messages = form.errors.get('__all__', [])
        for error in error_messages:
            if 'inactive' in str(error).lower():
                try:
                    user = User.objects.get(username=form.data.get('username'))
                    if not user.is_active:
                        messages.error(self.request, 'Please verify your email address before logging in. Check your inbox for the verification link.')
                        return redirect('verify_email_pending', user_id=user.pk)
                except User.DoesNotExist:
                    pass
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have logged out successfully.")
        response = super().dispatch(request, *args, **kwargs)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response


@ratelimit(key='ip', rate='5/m', block=True)
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_verification_email(user, request)
            messages.success(request, f"Account created! Please check your email ({user.email}) to verify your account before logging in.")
            return redirect('verify_email_pending', user_id=user.pk)
        else:
            messages.error(request, "Please correct the errors below to register.")
            logger.debug("Register form errors: %s", form.errors)
    else:
        form = UserRegisterForm()

    context = {'form': form}
    return render(request, 'yoga_app/registration/register.html', context)


def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        login(request, user)
        messages.success(request, "Email verified successfully! Welcome to Yoga Kailasa.")
        return redirect('home')
    else:
        messages.error(request, "Invalid or expired verification link. Please request a new one.")
        return redirect('home')


def verify_email_pending_view(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')

    if user.is_active:
        return redirect('login')

    if request.method == 'POST':
        send_verification_email(user, request)
        messages.success(request, f"Verification email sent to {user.email}.")
        return redirect('verify_email_pending', user_id=user.pk)

    context = {'user': user}
    return render(request, 'yoga_app/registration/verify_email_pending.html', context)


@login_required
def resend_verification_view(request):
    if request.user.is_active:
        messages.info(request, "Your email is already verified.")
        return redirect('dashboard')

    send_verification_email(request.user, request)
    messages.success(request, f"Verification email sent to {request.user.email}.")
    return redirect('verify_email_pending', user_id=request.user.pk)


@login_required
def profile_update_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if created:
        logger.info("Created UserProfile for %s during profile update view access.", request.user.username)

    if request.method == 'POST':
        user_account_form = UserAccountUpdateForm(request.POST, instance=request.user)
        user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

        profile_updated = False
        password_updated = False
        user_profile_updated = False

        if 'update_account' in request.POST:
            if user_account_form.is_valid():
                user_account_form.save()
                messages.success(request, 'Your account (username and email) has been updated successfully!')
                profile_updated = True
            else:
                messages.error(request, 'Error updating account. Please check the form.')

        if 'update_profile' in request.POST:
            if user_profile_form.is_valid():
                user_profile_form.save()
                request.user = get_user_model().objects.get(pk=request.user.pk)
                messages.success(request, 'Your profile picture and bio have been updated successfully!')
                user_profile_updated = True
            else:
                messages.error(request, 'Error updating profile. Please check the form.')

        if 'change_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password has been changed successfully!')
                password_updated = True
            else:
                messages.error(request, 'Error changing password. Please check the form.')

        if profile_updated or password_updated or user_profile_updated:
            return redirect('profile_edit')

    else:
        user_account_form = UserAccountUpdateForm(instance=request.user)
        user_profile_form = UserProfileForm(instance=user_profile)
        password_form = CustomPasswordChangeForm(user=request.user)

    context = {
        'user_account_form': user_account_form,
        'user_profile_form': user_profile_form,
        'password_form': password_form,
        'user_profile': user_profile,
    }
    return render(request, 'yoga_app/profile_edit.html', context)


@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')
    else:
        messages.error(request, 'Invalid request to delete account.')
        return redirect('dashboard')
