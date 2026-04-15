"""
Shared email sending utility.
Renders HTML templates and sends via Django's mail backend.
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_html_email(
    subject: str,
    template: str,
    context: dict,
    recipient: str,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> bool:
    """
    Render an HTML email template and send it.
    Falls back to a plain-text version automatically.

    Returns True on success, False on failure.
    """
    try:
        html_body = render_to_string(template, context)
        # Strip tags for plain-text fallback
        import re
        plain_body = re.sub(r'<[^>]+>', '', html_body)
        plain_body = re.sub(r'\n{3,}', '\n\n', plain_body).strip()

        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        msg.attach_alternative(html_body, 'text/html')
        for filename, data, mimetype in (attachments or []):
            msg.attach(filename, data, mimetype)
        msg.send(fail_silently=False)
        logger.info("Email '%s' sent to %s", subject, recipient)
        return True
    except Exception as exc:
        logger.error("Failed to send email '%s' to %s: %s", subject, recipient, exc)
        return False
