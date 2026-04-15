from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Count, Sum
from yoga_app.models import User, Course, Payment, UserLessonCompletion, UserCourseCompletion


class ReportService:
    @staticmethod
    def generate_progress_report(user):
        enrolled_courses = user.profile.enrolled_courses.all() if hasattr(user, 'profile') else []
        completed_courses = UserCourseCompletion.objects.filter(user=user).count()
        total_lessons_completed = UserLessonCompletion.objects.filter(user=user).count()

        course_progress = []
        for course in enrolled_courses:
            total_lessons = course.modules.aggregate(total=Count('lessons'))['total'] or 0
            completed = UserLessonCompletion.objects.filter(user=user, lesson__module__course=course).count()
            progress = int((completed / total_lessons) * 100) if total_lessons > 0 else 0
            course_progress.append({
                'title': course.title,
                'progress': progress,
                'completed_lessons': completed,
                'total_lessons': total_lessons,
            })

        return {
            'report_type': 'progress',
            'user': user.username,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'enrolled_courses': len(enrolled_courses),
            'completed_courses': completed_courses,
            'total_lessons_completed': total_lessons_completed,
            'course_details': course_progress,
        }

    @staticmethod
    def generate_payment_report(user):
        payments = Payment.objects.filter(user=user).select_related('course').order_by('-created_at')
        total_spent = payments.filter(status='success').aggregate(total=Sum('amount'))['total'] or 0

        payment_details = []
        for payment in payments:
            payment_details.append({
                'course': payment.course.title if payment.course else 'N/A',
                'amount': str(payment.amount),
                'status': payment.status,
                'date': payment.created_at.strftime('%Y-%m-%d'),
            })

        return {
            'report_type': 'payment',
            'user': user.username,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_spent': str(total_spent),
            'total_transactions': payments.count(),
            'payment_details': payment_details,
        }

    @staticmethod
    def generate_activity_report(user):
        from yoga_app.models import DiscussionTopic, DiscussionPost, BlogComment, LessonComment

        topics_created = DiscussionTopic.objects.filter(user=user).count()
        posts_created = DiscussionPost.objects.filter(user=user).count()
        blog_comments = BlogComment.objects.filter(user=user).count()
        lesson_comments = LessonComment.objects.filter(user=user).count()

        return {
            'report_type': 'activity',
            'user': user.username,
            'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'discussion_topics': topics_created,
            'discussion_posts': posts_created,
            'blog_comments': blog_comments,
            'lesson_comments': lesson_comments,
            'total_interactions': topics_created + posts_created + blog_comments + lesson_comments,
        }

    @staticmethod
    def format_report_as_text(report_data):
        lines = []
        lines.append(f"Report Type: {report_data['report_type'].title()}")
        lines.append(f"User: {report_data['user']}")
        lines.append(f"Generated: {report_data['generated_at']}")
        lines.append("=" * 50)
        lines.append("")

        for key, value in report_data.items():
            if key in ('report_type', 'user', 'generated_at'):
                continue
            if isinstance(value, list):
                lines.append(f"{key.replace('_', ' ').title()}:")
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            lines.append(f"  - {k.replace('_', ' ').title()}: {v}")
                    else:
                        lines.append(f"  - {item}")
                lines.append("")
            else:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")

        return "\n".join(lines)


@shared_task
def generate_report_task(report_type, user_email):
    from django.contrib.auth.models import User
    user = User.objects.filter(email=user_email).first()
    if not user:
        return

    if report_type == 'progress':
        report_data = ReportService.generate_progress_report(user)
    elif report_type == 'payment':
        report_data = ReportService.generate_payment_report(user)
    elif report_type == 'activity':
        report_data = ReportService.generate_activity_report(user)
    else:
        report_data = ReportService.generate_progress_report(user)

    report_text = ReportService.format_report_as_text(report_data)

    send_mail(
        f'Your {report_type.title()} Report is Ready',
        report_text,
        'no-reply@yogakailasa.com',
        [user_email],
        fail_silently=False,
    )
