from .views.auth_views import *
from .views.course_views import *
from .views.content_views import *
from .views.blog_views import *
from .views.discussion_views import *
from .views.payment_views import *
from .views.user_views import *
from .views.booking_views import *
from .views.feedback_views import *
from .views.search_views import *

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import cache_page
from yoga_app.forms import ContactMessageForm
from yoga_app.models import YogaPose, BreathingTechnique, Course, Consultant, Testimonial


def home_view(request):
    if messages.get_messages(request):
        yoga_poses = YogaPose.objects.all().order_by('?')[:3]
        breathing_techniques = BreathingTechnique.objects.all().order_by('name')
        courses = Course.objects.annotate_avg_rating().order_by('-is_popular', 'price') if hasattr(Course.objects, 'annotate_avg_rating') else Course.objects.order_by('-is_popular', 'price')
        consultants = Consultant.objects.all().order_by('name')
        testimonials = Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')[:3]
        contact_form = ContactMessageForm()

        context = {
            'yoga_poses': yoga_poses,
            'breathing_techniques': breathing_techniques,
            'courses': courses,
            'consultants': consultants,
            'testimonials': testimonials,
            'contact_form': contact_form,
        }
        response = render(request, 'yoga_app/index.html', context)
        return response

    @cache_page(60 * 5)
    def _home_view_cached(request):
        yoga_poses = YogaPose.objects.all().order_by('?')[:3]
        breathing_techniques = BreathingTechnique.objects.all().order_by('name')
        courses = Course.objects.order_by('-is_popular', 'price')
        consultants = Consultant.objects.all().order_by('name')
        testimonials = Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')[:3]
        contact_form = ContactMessageForm()

        context = {
            'yoga_poses': yoga_poses,
            'breathing_techniques': breathing_techniques,
            'courses': courses,
            'consultants': consultants,
            'testimonials': testimonials,
            'contact_form': contact_form,
        }
        return render(request, 'yoga_app/index.html', context)

    return _home_view_cached(request)
