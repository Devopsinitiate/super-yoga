# yoga_app/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView, CustomLogoutView
from .forms import UserLoginForm

urlpatterns = [
    path('', views.home_view, name='home'),
    path('booking/', views.booking_view, name='booking'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('newsletter-subscribe/', views.newsletter_subscribe_view, name='newsletter_subscribe'),

    path('poses/', views.pose_list_view, name='poses'),
    path('poses/<int:pose_id>/', views.pose_detail_view, name='pose_detail'),
    
    path('breathing/', views.breathing_list_view, name='breathing'),
    path('breathing/<int:technique_id>/', views.breathing_technique_detail_view, name='breathing_technique_detail'),
    
    path('courses/', views.course_list_view, name='courses'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    
    path('courses/<int:course_id>/content/', views.course_content_view, name='course_content_base'),
    path('courses/<int:course_id>/content/<int:lesson_id>/', views.course_content_view, name='course_content'),

    path('courses/initiate-payment/<int:course_id>/', views.initiate_payment_view, name='initiate_payment'),
    path('payments/verify/', views.verify_payment_view, name='verify_payment'),
    path('payments/webhook/paystack/', views.paystack_webhook_view, name='paystack_webhook'),
    path('payments/webhook/paystack', views.paystack_webhook_view),  # no-slash variant for Paystack

    path('register/', views.register_view, name='register'),
    path('verify-email/<uidb64>/<token>/', views.verify_email_view, name='verify_email'),
    path('verify-email/pending/<int:user_id>/', views.verify_email_pending_view, name='verify_email_pending'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),
    path('login/', CustomLoginView.as_view(template_name='yoga_app/registration/login.html', authentication_form=UserLoginForm), name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='home'), name='logout'),

    path('dashboard/', views.user_dashboard_view, name='dashboard'),

    path('enroll/free/<int:course_id>/', views.enroll_free_course_view, name='enroll_free_course'),

    path('courses/complete/<int:course_id>/', views.mark_course_complete_view, name='mark_course_complete'),

    path('courses/<int:course_id>/lessons/<int:lesson_id>/complete/', views.mark_lesson_complete_view, name='mark_lesson_complete'),

    path('courses/<int:course_id>/discussion/', views.course_discussion_list_view, name='course_discussion_list'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/', views.discussion_topic_detail_view, name='course_discussion_detail'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/edit/', views.edit_discussion_topic_view, name='edit_discussion_topic'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/delete/', views.delete_discussion_topic_view, name='delete_discussion_topic'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/posts/<int:post_id>/edit/', views.edit_discussion_post_view, name='edit_discussion_post'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/posts/<int:post_id>/delete/', views.delete_discussion_post_view, name='delete_discussion_post'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/like/', views.toggle_topic_like, name='toggle_topic_like'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/posts/<int:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),

    path('notifications/api/', views.get_notifications_api, name='get_notifications_api'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/', views.all_notifications_view, name='all_notifications'),

    path('profile/edit/', views.profile_update_view, name='profile_edit'),
    path('certificate/<int:course_id>/', views.download_certificate_view, name='download_certificate'),

    path('search/', views.global_search_view, name='global_search'),
    path('search/suggestions/', views.global_search_suggestions_api, name='global_search_suggestions_api'),

    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),

    # ── Wellness Library ──────────────────────────────────────────────────────
    path('mudras/', views.mudra_list_view, name='mudras'),
    path('mudras/<int:mudra_id>/', views.mudra_detail_view, name='mudra_detail'),
    path('meditations/', views.meditation_list_view, name='meditations'),
    path('meditations/<int:meditation_id>/', views.meditation_detail_view, name='meditation_detail'),
    path('chakras/', views.chakra_guide_view, name='chakra_guide'),
    path('practice/', views.daily_practice_view, name='daily_practice'),
    path('practice/log/', views.log_practice_view, name='log_practice'),

    # ── Kriya Sessions ────────────────────────────────────────────────────────
    path('kriyas/', views.kriya_list_view, name='kriyas'),
    path('kriyas/<int:kriya_id>/', views.kriya_detail_view, name='kriya_detail'),

    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='yoga_app/registration/password_reset_form.html',
             email_template_name='yoga_app/registration/password_reset_email.html',
             html_email_template_name='registration/password_reset_email.html',
             subject_template_name='yoga_app/registration/password_reset_subject.txt',
             success_url='/password_reset/done/'
         ),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='yoga_app/registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='yoga_app/registration/password_reset_confirm.html',
             success_url='/reset/done/'
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='yoga_app/registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('account/delete/', views.delete_account_view, name='delete_account'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),

    path('courses/<int:course_id>/review/submit/', views.submit_course_review_view, name='submit_course_review'),

    path('blog/', views.blog_list_view, name='blog_list'),
    path('blog/new/', views.create_blog_post_view, name='create_blog_post'),
    path('blog/my-posts/', views.my_blog_posts_view, name='my_blog_posts'),
    path('blog/<slug:post_slug>/', views.blog_detail_view, name='blog_detail'),
    path('blog/<slug:post_slug>/edit/', views.edit_blog_post_view, name='edit_blog_post'),
    path('blog/<slug:post_slug>/delete/', views.delete_blog_post_view, name='delete_blog_post'),
    path('blog/<slug:post_slug>/comment/', views.add_blog_comment_view, name='add_blog_comment'),
    path('blog/<slug:post_slug>/like/', views.toggle_blog_post_like, name='toggle_blog_post_like'),

    path('consultants/', views.consultant_list_view, name='consultant_list'),
    path('consultants/<int:consultant_id>/', views.consultant_detail_view, name='consultant_detail'),

    path('request-report/', views.request_report_view, name='request_report'),

    # ── Teacher / Staff Booking Management ───────────────────────────────────
    path('teacher/bookings/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('teacher/bookings/<int:booking_id>/', views.booking_detail_view, name='teacher_booking_detail'),
    path('teacher/bookings/<int:booking_id>/status/', views.update_booking_status_view, name='teacher_update_booking_status'),
]