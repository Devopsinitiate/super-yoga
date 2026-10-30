"""
Yoga Kailasa — Custom middleware.
"""
import logging
import secrets

logger = logging.getLogger(__name__)


class ContentSecurityPolicyMiddleware:
    """
    Adds a Content-Security-Policy header to every response.

    Allows:
    - Self-hosted assets
    - Google Fonts (fonts.googleapis.com, fonts.gstatic.com)
    - YouTube embeds (youtube.com, youtube-nocookie.com)
    - Vimeo, Instagram, TikTok and Facebook video embeds
    - Paystack JS (js.paystack.co)
    - Font Awesome CDN (cdnjs.cloudflare.com)
    - CKEditor uploads (same origin)

    A per-request nonce is generated and attached to request.csp_nonce;
    inline <script nonce="{{ request.csp_nonce }}"> blocks inherit it,
    so script-src does not need 'unsafe-inline'. All inline event handlers
    must use data-action delegation (see kailasa.js) instead.

    Configured via settings.CSP_EXTRA_SCRIPT_SRC / CSP_EXTRA_FRAME_SRC
    for environment-specific overrides (e.g. ngrok in development).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        from django.conf import settings
        # Allow extra origins to be injected per environment
        self._extra_script = getattr(settings, 'CSP_EXTRA_SCRIPT_SRC', '')
        self._extra_frame = getattr(settings, 'CSP_EXTRA_FRAME_SRC', '')
        self._debug = getattr(settings, 'DEBUG', False)

    def __call__(self, request):
        # Per-request nonce for inline <script> blocks (set BEFORE the view runs
        # so templates referenced by views can read it via the context processor)
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        # Don't add CSP to admin — it uses inline styles/scripts
        if request.path.startswith('/admin/'):
            return response
        response['Content-Security-Policy'] = self._build_csp(request.csp_nonce)
        return response

    def _build_csp(self, nonce: str) -> str:
        extra_script = f" {self._extra_script}" if self._extra_script else ''
        extra_frame = f" {self._extra_frame}" if self._extra_frame else ''

        directives = [
            "default-src 'self'",
            f"script-src 'self' https://js.paystack.co https://cdnjs.cloudflare.com https://www.youtube.com https://s.ytimg.com 'nonce-{nonce}'{extra_script}",
            f"style-src 'self' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://paystack.com 'unsafe-inline'",
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:",
            f"frame-src 'self' https://www.youtube.com https://youtube.com https://www.youtube-nocookie.com https://js.paystack.co https://checkout.paystack.com https://player.vimeo.com https://www.instagram.com https://www.tiktok.com https://www.facebook.com{extra_frame}",
            "img-src 'self' data: https: blob:",
            f"connect-src 'self' https://api.paystack.co https://www.youtube.com https://www.googleapis.com",
            "media-src 'self' https:",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests" if not self._debug else "",
        ]
        return '; '.join(d for d in directives if d)


class UserProfileMiddleware:
    """
    Attaches the UserProfile to request.user_profile for authenticated requests.
    Eliminates repeated get_object_or_404(UserProfile, user=request.user) calls in views.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_profile = None
        if request.user.is_authenticated:
            try:
                from yoga_app.models import UserProfile
                request.user_profile = UserProfile.objects.select_related('user').get(
                    user=request.user
                )
            except Exception:
                # Profile may not exist yet — views handle this gracefully
                pass
        return self.get_response(request)
