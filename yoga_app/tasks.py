import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from yoga_app.utils.email import send_html_email
from yoga_app.utils.certificate import generate_certificate

logger = logging.getLogger(__name__)


# ─── Enrollment Confirmation ──────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_enrollment_confirmation_email(self, user_id: int, course_id: int):
    """Send an enrollment confirmation email after a user enrolls in a course."""
    try:
        from django.contrib.auth.models import User
        from yoga_app.models import Course
        from django.urls import reverse

        user = User.objects.get(pk=user_id)
        course = Course.objects.get(pk=course_id)

        send_html_email(
            subject=f"You're enrolled in {course.title} — Yoga Kailasa",
            template='yoga_app/emails/enrollment_confirmation.html',
            context={
                'username': user.username,
                'course_title': course.title,
                'instructor_name': course.instructor_name,
                'course_duration': course.duration,
                'is_free': course.is_free,
                'amount_paid': course.price,
                'dashboard_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/dashboard/",
            },
            recipient=user.email,
        )
    except Exception as exc:
        logger.error("Enrollment confirmation failed for user %s course %s: %s", user_id, course_id, exc)
        raise self.retry(exc=exc)


# ─── Course Completion ────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_course_completion_email(self, user_id: int, course_id: int):
    """Send a congratulations email when a user completes a course."""
    try:
        from django.contrib.auth.models import User
        from yoga_app.models import Course

        user = User.objects.get(pk=user_id)
        course = Course.objects.get(pk=course_id)

        pdf_bytes = generate_certificate(user, course)
        if pdf_bytes:
            attachments = [(f"certificate_{getattr(course, 'slug', course.id)}.pdf", pdf_bytes, "application/pdf")]
        else:
            attachments = []

        send_html_email(
            subject=f"Congratulations — You completed {course.title}!",
            template='yoga_app/emails/course_completion.html',
            context={
                'username': user.username,
                'course_title': course.title,
                'completed_date': timezone.now().strftime('%B %d, %Y'),
                'courses_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/courses/",
            },
            recipient=user.email,
            attachments=attachments,
        )
    except Exception as exc:
        logger.error("Course completion email failed for user %s course %s: %s", user_id, course_id, exc)
        raise self.retry(exc=exc)


# ─── Booking Confirmation ─────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_booking_confirmation_email(self, booking_id: int):
    """Send a booking confirmation email to the user."""
    try:
        from yoga_app.models import Booking

        booking = Booking.objects.get(pk=booking_id)

        send_html_email(
            subject=f"Booking Confirmed — {booking.preferred_date} — Yoga Kailasa",
            template='yoga_app/emails/booking_confirmation.html',
            context={
                'full_name': booking.full_name,
                'booking_id': booking.id,
                'preferred_date': booking.preferred_date.strftime('%A, %B %d, %Y'),
                'preferred_time': booking.preferred_time,
                'message': booking.message or '',
            },
            recipient=booking.email,
        )
    except Exception as exc:
        logger.error("Booking confirmation email failed for booking #%s: %s", booking_id, exc)
        raise self.retry(exc=exc)


# ─── New Blog Post Alert ──────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def send_new_blog_post_notifications(self, post_id: int):
    """
    Notify all active newsletter subscribers about a new blog post.
    Sends in batches to avoid memory issues with large subscriber lists.
    """
    try:
        from yoga_app.models import BlogPost, NewsletterSubscription

        post = BlogPost.objects.select_related('author', 'category').get(pk=post_id)
        if not post.is_published:
            logger.info("Skipping blog notification — post %s is not published", post_id)
            return

        site_url = getattr(settings, 'SITE_URL', '')
        context = {
            'post_title': post.title,
            'excerpt': post.excerpt or '',
            'author_name': post.author.get_full_name() or post.author.username,
            'published_date': post.published_date.strftime('%B %d, %Y') if post.published_date else '',
            'category_name': post.category.name if post.category else '',
            'post_url': f"{site_url}/blog/{post.slug}/",
            'featured_image_url': post.featured_image.url if post.featured_image else '',
        }

        subscribers = NewsletterSubscription.objects.filter(
            is_active=True
        ).values_list('email', flat=True)

        sent = 0
        failed = 0
        for email in subscribers:
            success = send_html_email(
                subject=f"New post: {post.title} — Yoga Kailasa Journal",
                template='yoga_app/emails/new_blog_post.html',
                context=context,
                recipient=email,
            )
            if success:
                sent += 1
            else:
                failed += 1

        logger.info(
            "Blog post notification for '%s': %d sent, %d failed",
            post.title, sent, failed
        )
    except Exception as exc:
        logger.error("Blog post notification task failed for post %s: %s", post_id, exc)
        raise self.retry(exc=exc)


# ─── Newsletter ───────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_newsletter_email(self, subject: str, message: str, recipient_list: list):
    """Send a plain-text newsletter to a list of recipients."""
    try:
        from django.core.mail import send_mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        logger.info("Newsletter sent to %d recipients", len(recipient_list))
    except Exception as exc:
        logger.error("Newsletter send failed: %s", exc)
        raise self.retry(exc=exc)


# ─── Report Generation ────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_report_task(self, report_type: str, user_email: str):
    """Generate a report and notify the user by email when ready."""
    try:
        from yoga_app.services.report_service import ReportService
        from django.core.mail import send_mail

        report_content = ReportService.generate(report_type)
        send_mail(
            subject=f'Your {report_type.title()} Report is Ready — Yoga Kailasa',
            message=(
                f'Your {report_type} report has been generated.\n\n'
                f'{report_content}\n\n'
                'Log in to your dashboard to view the full report.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info("Report '%s' sent to %s", report_type, user_email)
    except Exception as exc:
        logger.error("Report generation failed for type '%s': %s", report_type, exc)
        raise self.retry(exc=exc)


# ─── Profile Picture Optimization ────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def optimize_profile_picture_task(self, profile_pk: int):
    """Optimize a user's profile picture after upload."""
    try:
        import os
        from yoga_app.models import UserProfile
        from yoga_app.utils.image_optimize import optimize_image

        profile = UserProfile.objects.get(pk=profile_pk)
        if not profile.profile_picture:
            return

        optimized_path = optimize_image(profile.profile_picture.path)
        new_name = os.path.relpath(optimized_path, settings.MEDIA_ROOT)
        if new_name != profile.profile_picture.name:
            UserProfile.objects.filter(pk=profile_pk).update(profile_picture=new_name)
            logger.info("Profile picture optimized for UserProfile pk=%s", profile_pk)
    except Exception as exc:
        logger.error("Profile picture optimization failed for pk=%s: %s", profile_pk, exc)
        raise self.retry(exc=exc)
