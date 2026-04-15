import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from yoga_app.models import UserProfile, Payment, Notification
from yoga_app.services import ProgressService, NotificationService

logger = logging.getLogger(__name__)


@login_required
def user_dashboard_view(request):
    dashboard_data = ProgressService.get_user_dashboard_data(request.user)
    payment_history = Payment.objects.filter(
        user=request.user
    ).select_related('course').order_by('-paid_at')
    recent_notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender').order_by('-created_at')[:5]
    unread_notifications_count = Notification.objects.filter(
        recipient=request.user, read=False
    ).count()

    # Booking history — uses the new Booking.user FK
    from yoga_app.models import Booking
    booking_history = Booking.objects.filter(
        user=request.user
    ).order_by('-booked_at')[:5]

    # Recent activity — last 5 completed lessons
    from yoga_app.models import UserLessonCompletion
    recent_completions = UserLessonCompletion.objects.filter(
        user=request.user
    ).select_related('lesson__module__course').order_by('-completed_at')[:5]

    context = {
        'enrolled_courses_data': dashboard_data['enrolled_courses_data'],
        'user_profile': dashboard_data['user_profile'],
        'payment_history': payment_history,
        'last_viewed_lesson': dashboard_data['last_viewed_lesson'],
        'recent_notifications': recent_notifications,
        'unread_notifications_count': unread_notifications_count,
        'completed_courses_count': dashboard_data['completed_courses_count'],
        'booking_history': booking_history,
        'recent_completions': recent_completions,
    }
    return render(request, 'yoga_app/user_dashboard.html', context)


@login_required
@ratelimit(key='user', rate='30/m', block=True)
def get_notifications_api(request):
    notifications_data = NotificationService.get_notifications_for_api(request.user)
    return JsonResponse({'notifications': notifications_data})


@login_required
@ratelimit(key='user', rate='60/m', block=True)
def mark_notification_read_view(request, notification_id):
    if request.method == 'POST':
        try:
            success = NotificationService.mark_as_read(request.user, notification_id)
            if success:
                return JsonResponse({'status': 'success', 'message': 'Notification marked as read.'})
            return JsonResponse({'status': 'success', 'message': 'Notification already read or not found.'})
        except Exception as e:
            logger.exception("Failed to mark notification %s as read: %s", notification_id, e)
            return JsonResponse({'status': 'error', 'message': 'Failed to mark notification as read.'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
def all_notifications_view(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender').order_by('read', '-created_at')

    # Mark all unread as read on page load
    Notification.objects.filter(recipient=request.user, read=False).update(read=True)

    context = {'notifications': notifications}
    return render(request, 'yoga_app/all_notifications.html', context)


@login_required
@ratelimit(key='user', rate='5/h', block=True)
def request_report_view(request):
    from yoga_app.tasks import generate_report_task
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'progress')
        user_email = request.user.email
        if user_email:
            generate_report_task.delay(report_type, user_email)
            messages.success(
                request,
                f"Your {report_type} report is being generated and will be sent to {user_email}."
            )
        else:
            messages.error(request, "No email address found. Please update your profile.")
        return redirect('dashboard')
    return render(request, 'yoga_app/request_report.html')


@login_required
def download_certificate_view(request, course_id):
    """Generate and serve a PDF certificate for a completed course."""
    from django.http import HttpResponse, Http404
    from yoga_app.models import Course, UserCourseCompletion
    from yoga_app.utils.certificate import generate_certificate

    course = get_object_or_404(Course, id=course_id)

    # Must be enrolled and have completed the course
    if not UserCourseCompletion.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "You have not completed this course yet.")
        return redirect('dashboard')

    pdf_bytes = generate_certificate(request.user, course)
    if not pdf_bytes:
        messages.error(request, "Certificate could not be generated. Please try again.")
        return redirect('dashboard')

    filename = f"certificate_{getattr(course, 'slug', course.id)}.pdf"
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
