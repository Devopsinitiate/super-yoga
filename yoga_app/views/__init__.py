from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from yoga_app.forms import ContactMessageForm
from yoga_app.models import YogaPose, BreathingTechnique, Course, Consultant, Testimonial


def _build_home_context(request):
    return {
        'yoga_poses': YogaPose.objects.all().order_by('?')[:3],
        'breathing_techniques': BreathingTechnique.objects.all().order_by('name'),
        'courses': Course.objects.order_by('-is_popular', 'price'),
        'consultants': Consultant.objects.all().order_by('name'),
        'testimonials': Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')[:3],
        'contact_form': ContactMessageForm(),
    }


def home_view(request):
    # If there are flash messages pending, skip cache so they display immediately
    if list(messages.get_messages(request)):
        return render(request, 'yoga_app/index.html', _build_home_context(request))
    return _cached_home_view(request)


@vary_on_cookie
@cache_page(60 * 5)
def _cached_home_view(request):
    return render(request, 'yoga_app/index.html', _build_home_context(request))


from .auth_views import (
    CustomLoginView,
    CustomLogoutView,
    register_view,
    verify_email_view,
    verify_email_pending_view,
    resend_verification_view,
    profile_update_view,
    delete_account_view,
)

from .course_views import (
    course_list_view,
    course_detail_view,
    course_content_view,
    submit_course_review_view,
    enroll_free_course_view,
    mark_course_complete_view,
    mark_lesson_complete_view,
)

from .content_views import (
    pose_list_view,
    pose_detail_view,
    breathing_list_view,
    breathing_technique_detail_view,
)

from .blog_views import (
    blog_list_view,
    blog_detail_view,
    add_blog_comment_view,
    toggle_blog_post_like,
    create_blog_post_view,
    edit_blog_post_view,
    my_blog_posts_view,
    delete_blog_post_view,
)

from .discussion_views import (
    course_discussion_list_view,
    discussion_topic_detail_view,
    edit_discussion_topic_view,
    delete_discussion_topic_view,
    edit_discussion_post_view,
    delete_discussion_post_view,
    toggle_topic_like,
    toggle_post_like,
)

from .payment_views import (
    initiate_payment_view,
    verify_payment_view,
    paystack_webhook_view,
)

from .user_views import (
    user_dashboard_view,
    get_notifications_api,
    mark_notification_read_view,
    all_notifications_view,
    request_report_view,
    download_certificate_view,
)

from .booking_views import (
    consultant_list_view,
    consultant_detail_view,
    booking_view,
)

from .feedback_views import (
    feedback_view,
    newsletter_subscribe_view,
    contact_view,
)

from .search_views import (
    global_search_view,
    global_search_suggestions_api,
    about_view,
    privacy_policy_view,
    terms_of_service_view,
)

from .wellness_views import (
    mudra_list_view,
    mudra_detail_view,
    meditation_list_view,
    meditation_detail_view,
    chakra_guide_view,
    daily_practice_view,
    log_practice_view,
    kriya_list_view,
    kriya_detail_view,
)

from .teacher_views import (
    teacher_dashboard_view,
    booking_detail_view,
    update_booking_status_view,
)

__all__ = [
    'home_view',
    'CustomLoginView',
    'CustomLogoutView',
    'register_view',
    'verify_email_view',
    'verify_email_pending_view',
    'resend_verification_view',
    'profile_update_view',
    'delete_account_view',
    'course_list_view',
    'course_detail_view',
    'course_content_view',
    'submit_course_review_view',
    'enroll_free_course_view',
    'mark_course_complete_view',
    'mark_lesson_complete_view',
    'pose_list_view',
    'pose_detail_view',
    'breathing_list_view',
    'breathing_technique_detail_view',
    'blog_list_view',
    'blog_detail_view',
    'add_blog_comment_view',
    'toggle_blog_post_like',
    'course_discussion_list_view',
    'discussion_topic_detail_view',
    'edit_discussion_topic_view',
    'delete_discussion_topic_view',
    'edit_discussion_post_view',
    'delete_discussion_post_view',
    'toggle_topic_like',
    'toggle_post_like',
    'initiate_payment_view',
    'verify_payment_view',
    'paystack_webhook_view',
    'user_dashboard_view',
    'get_notifications_api',
    'mark_notification_read_view',
    'all_notifications_view',
    'request_report_view',
    'consultant_list_view',
    'consultant_detail_view',
    'booking_view',
    'feedback_view',
    'newsletter_subscribe_view',
    'contact_view',
    'global_search_view',
    'global_search_suggestions_api',
    'about_view',
]
