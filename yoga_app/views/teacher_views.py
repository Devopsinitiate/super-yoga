"""
Teacher / Staff booking management views.
Access restricted to users with is_staff=True.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count

from yoga_app.models import Booking

logger = logging.getLogger(__name__)

# ── Access guard ──────────────────────────────────────────────────────────────

def is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

staff_required = user_passes_test(is_staff, login_url='login')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
@staff_required
def teacher_dashboard_view(request):
    """Main booking management dashboard for teachers/staff."""
    today = timezone.localdate()

    # Filters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    search = request.GET.get('q', '')

    bookings = Booking.objects.select_related('user').order_by('preferred_date', 'preferred_time')

    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if date_filter:
        bookings = bookings.filter(preferred_date=date_filter)
    if search:
        bookings = bookings.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(message__icontains=search)
        )

    # Stats
    stats = {
        'total': Booking.objects.count(),
        'pending': Booking.objects.filter(status='pending').count(),
        'confirmed': Booking.objects.filter(status='confirmed').count(),
        'today': Booking.objects.filter(preferred_date=today).count(),
        'upcoming': Booking.objects.filter(
            preferred_date__gte=today, status__in=['pending', 'confirmed']
        ).count(),
    }

    context = {
        'bookings': bookings,
        'stats': stats,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search': search,
        'today': today,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'yoga_app/teacher/dashboard.html', context)


# ── Booking detail / update ───────────────────────────────────────────────────

@login_required
@staff_required
def booking_detail_view(request, booking_id):
    """View and update a single booking."""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        teacher_notes = request.POST.get('teacher_notes', '')

        if new_status in dict(Booking.STATUS_CHOICES):
            old_status = booking.status
            booking.status = new_status
            booking.teacher_notes = teacher_notes
            booking.save(update_fields=['status', 'teacher_notes', 'updated_at'])
            logger.info(
                "Booking #%s status changed from %s to %s by %s",
                booking.id, old_status, new_status, request.user.username
            )
            messages.success(request, f"Booking #{booking.id} updated to '{booking.get_status_display()}'.")
        else:
            messages.error(request, "Invalid status.")

        return redirect('teacher_booking_detail', booking_id=booking.id)

    context = {
        'booking': booking,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'yoga_app/teacher/booking_detail.html', context)


# ── Quick status update (AJAX) ────────────────────────────────────────────────

@login_required
@staff_required
def update_booking_status_view(request, booking_id):
    """AJAX endpoint to update booking status inline from the dashboard."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('status')

    if new_status not in dict(Booking.STATUS_CHOICES):
        return JsonResponse({'error': 'Invalid status'}, status=400)

    booking.status = new_status
    booking.save(update_fields=['status', 'updated_at'])
    logger.info("Booking #%s quick-updated to %s by %s", booking.id, new_status, request.user.username)

    return JsonResponse({
        'success': True,
        'status': booking.status,
        'status_display': booking.get_status_display(),
    })
