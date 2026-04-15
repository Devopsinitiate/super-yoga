from django.shortcuts import render, redirect
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from yoga_app.forms import TestimonialForm, NewsletterSubscriptionForm, ContactMessageForm
from yoga_app.models import Testimonial
from yoga_app.tasks import send_newsletter_email


def feedback_view(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your valuable feedback! It will be reviewed shortly.')
            return redirect('feedback')
        else:
            messages.error(request, 'There was an error submitting your feedback. Please ensure all required fields are filled.')
    else:
        form = TestimonialForm()
    
    approved_testimonials = Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')

    context = {
        'form': form,
        'testimonials': approved_testimonials,
    }
    return render(request, 'yoga_app/feedback.html', context)


def newsletter_subscribe_view(request):
    if request.method == 'POST':
        form = NewsletterSubscriptionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            form.save()
            send_newsletter_email.delay(
                'Welcome to Yoga Kailasa Newsletter!',
                'Thank you for subscribing to our newsletter.',
                [email]
            )
            messages.success(request, 'Thank you for subscribing to our newsletter!')
            return redirect('home')
        else:
            if 'email' in form.errors and any('already exists' in e for e in form.errors['email']):
                messages.info(request, 'You are already subscribed to our newsletter!')
            else:
                messages.error(request, 'Please enter a valid email address to subscribe.')
            return redirect('home')
    return redirect('home')


@ratelimit(key='ip', rate='3/m', block=True)
def contact_view(request):
    from yoga_app.forms import ContactMessageForm
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
            return redirect('contact')
        else:
            messages.error(request, 'There was an error sending your message. Please correct the highlighted fields.')
    else:
        form = ContactMessageForm()

    context = {'form': form}
    return render(request, 'yoga_app/contact.html', context)
