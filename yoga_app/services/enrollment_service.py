import logging
from django.db import IntegrityError, transaction
from django.utils import timezone
from yoga_app.models import UserProfile, Course, Lesson, UserLessonCompletion, UserCourseCompletion

logger = logging.getLogger(__name__)


class EnrollmentService:

    @staticmethod
    def get_or_create_profile(user) -> UserProfile:
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            logger.info("Created UserProfile for user: %s", user.username)
        return profile

    @staticmethod
    def is_enrolled(user, course) -> bool:
        if not user.is_authenticated:
            return False
        profile = EnrollmentService.get_or_create_profile(user)
        return profile.enrolled_courses.filter(id=course.id).exists()

    @staticmethod
    def enroll_user(user, course) -> tuple[bool, str]:
        profile = EnrollmentService.get_or_create_profile(user)
        if profile.enrolled_courses.filter(id=course.id).exists():
            return False, 'already_enrolled'
        profile.enrolled_courses.add(course)
        logger.info("User %s enrolled in course: %s", user.username, course.title)
        return True, 'enrolled'

    @staticmethod
    def enroll_free_course(user, course) -> tuple[bool, str]:
        if not course.is_free:
            return False, 'not_free'

        profile = EnrollmentService.get_or_create_profile(user)
        if profile.enrolled_courses.filter(id=course.id).exists():
            return False, 'already_enrolled'

        try:
            with transaction.atomic():
                from yoga_app.models import Payment
                reference = f"FREE-{course.id}-{user.id}-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
                Payment.objects.create(
                    user=user,
                    course=course,
                    amount=0.00,
                    reference=reference,
                    status='success',
                    paid_at=timezone.now(),
                    verified_at=timezone.now(),
                )
                profile.enrolled_courses.add(course)
                logger.info("User %s enrolled in free course: %s", user.username, course.title)
                # Send confirmation email async
                try:
                    from yoga_app.tasks import send_enrollment_confirmation_email
                    send_enrollment_confirmation_email.delay(user.id, course.id)
                except Exception:
                    pass
                return True, 'enrolled'
        except IntegrityError:
            return False, 'already_enrolled'

    @staticmethod
    def mark_lesson_complete(user, lesson) -> tuple[bool, str]:
        if UserLessonCompletion.objects.filter(user=user, lesson=lesson).exists():
            return False, 'already_complete'
        try:
            with transaction.atomic():
                UserLessonCompletion.objects.create(user=user, lesson=lesson)
                return True, 'completed'
        except IntegrityError:
            return False, 'already_complete'

    @staticmethod
    def mark_course_complete(user, course) -> tuple[bool, str]:
        if UserCourseCompletion.objects.filter(user=user, course=course).exists():
            return False, 'already_complete'

        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_count = UserLessonCompletion.objects.filter(
            user=user, lesson__module__course=course
        ).count()

        if total_lessons > 0 and completed_count < total_lessons:
            return False, 'lessons_incomplete'

        try:
            with transaction.atomic():
                UserCourseCompletion.objects.create(user=user, course=course)
                logger.info("User %s completed course: %s", user.username, course.title)

                # Try Celery first; fall back to synchronous send if unavailable
                celery_dispatched = False
                try:
                    from yoga_app.tasks import send_course_completion_email
                    send_course_completion_email.delay(user.id, course.id)
                    celery_dispatched = True
                except Exception:
                    pass

                if not celery_dispatched:
                    # Synchronous fallback — generate certificate and send email inline
                    try:
                        from yoga_app.utils.certificate import generate_certificate
                        from yoga_app.utils.email import send_html_email
                        from django.utils import timezone as tz
                        from django.conf import settings

                        pdf_bytes = generate_certificate(user, course)
                        attachments = []
                        if pdf_bytes:
                            attachments = [(
                                f"certificate_{getattr(course, 'slug', course.id)}.pdf",
                                pdf_bytes,
                                "application/pdf",
                            )]

                        send_html_email(
                            subject=f"Congratulations — You completed {course.title}!",
                            template='yoga_app/emails/course_completion.html',
                            context={
                                'username': user.username,
                                'course_title': course.title,
                                'completed_date': tz.now().strftime('%B %d, %Y'),
                                'courses_url': f"{getattr(settings, 'SITE_URL', '')}/courses/",
                            },
                            recipient=user.email,
                            attachments=attachments,
                        )
                        logger.info("Completion email sent synchronously for user %s course %s", user.id, course.id)
                    except Exception as e:
                        logger.warning("Synchronous completion email failed for user %s: %s", user.username, e)

                return True, 'completed'
        except IntegrityError:
            return False, 'already_complete'

    @staticmethod
    def update_last_viewed_lesson(user, lesson) -> None:
        profile = EnrollmentService.get_or_create_profile(user)
        if profile.last_viewed_lesson_id != lesson.pk:
            profile.last_viewed_lesson = lesson
            profile.save(update_fields=['last_viewed_lesson'])
