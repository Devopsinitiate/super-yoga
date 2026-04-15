from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from yoga_app.models import Consultant
from yoga_app.forms import BookingForm
from yoga_app.tasks import send_booking_confirmation_email


def consultant_list_view(request):
    consultants = Consultant.objects.all().order_by('name')
    
    query = request.GET.get('q')
    if query:
        consultants = consultants.filter(
            Q(name__icontains=query) |
            Q(specialty__icontains=query) |
            Q(bio__icontains=query)
        )
    
    context = {
        'consultants': consultants,
        'query': query,
    }
    return render(request, 'yoga_app/consultant_list.html', context)


def consultant_detail_view(request, consultant_id):
    consultant = get_object_or_404(Consultant, pk=consultant_id)
    context = {'consultant': consultant}
    return render(request, 'yoga_app/consultant_detail.html', context)


def booking_view(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            # Link to authenticated user when available
            if request.user.is_authenticated:
                booking.user = request.user
            booking.save()
            try:
                send_booking_confirmation_email.delay(booking.id)
            except Exception:
                pass
            messages.success(request, 'Your booking request has been submitted successfully! We will contact you shortly.')
            return redirect('booking')
        else:
            messages.error(request, 'There was an error with your booking. Please correct the errors below.')
    else:
        form = BookingForm()

    consultants = Consultant.objects.filter(is_available=True).order_by('name')
    context = {'form': form, 'consultants': consultants}
    return render(request, 'yoga_app/booking_page.html', context)
