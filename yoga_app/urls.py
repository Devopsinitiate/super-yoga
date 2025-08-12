# yoga_app/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView, CustomLogoutView # Import your custom views

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
    
    # Updated: course_content now accepts an optional lesson_id
    path('courses/<int:course_id>/content/', views.course_content_view, name='course_content_base'), # Base URL
    path('courses/<int:course_id>/content/<int:lesson_id>/', views.course_content_view, name='course_content'), # With lesson_id

    path('courses/initiate-payment/<int:course_id>/', views.initiate_payment_view, name='initiate_payment'),
    path('payments/verify/', views.verify_payment_view, name='verify_payment'),
    path('payments/webhook/paystack/', views.paystack_webhook_view, name='paystack_webhook'),

    # Authentication URLs
    path('register/', views.register_view, name='register'),
    # Use your custom login/logout views
    path('login/', CustomLoginView.as_view(template_name='yoga_app/registration/login.html', authentication_form=views.UserLoginForm), name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='home'), name='logout'),

    # User Dashboard URL
    path('dashboard/', views.user_dashboard_view, name='dashboard'),

    # URL for free course enrollment
    path('enroll/free/<int:course_id>/', views.enroll_free_course_view, name='enroll_free_course'),

    # URL to mark a course as complete
    path('courses/complete/<int:course_id>/', views.mark_course_complete_view, name='mark_course_complete'),

    # URL to mark a lesson as complete
    path('courses/<int:course_id>/lessons/<int:lesson_id>/complete/', views.mark_lesson_complete_view, name='mark_lesson_complete'),

    # Discussion Forum URLs
    path('courses/<int:course_id>/discussion/', views.course_discussion_list_view, name='course_discussion_list'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/', views.discussion_topic_detail_view, name='course_discussion_detail'),
    # URLs for editing and deleting discussion topics
    path('courses/<int:course_id>/discussion/<int:topic_id>/edit/', views.edit_discussion_topic_view, name='edit_discussion_topic'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/delete/', views.delete_discussion_topic_view, name='delete_discussion_topic'),
    # URLs for editing and deleting discussion posts
    path('courses/<int:course_id>/discussion/<int:topic_id>/posts/<int:post_id>/edit/', views.edit_discussion_post_view, name='edit_discussion_post'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/posts/<int:post_id>/delete/', views.delete_discussion_post_view, name='delete_discussion_post'),
    # NEW: URLs for liking/unliking discussion topics and posts (AJAX endpoints)
    path('courses/<int:course_id>/discussion/<int:topic_id>/like/', views.toggle_topic_like, name='toggle_topic_like'),
    path('courses/<int:course_id>/discussion/<int:topic_id>/posts/<int:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),

    # NEW: Notification URLs (AJAX endpoints)
    path('notifications/api/', views.get_notifications_api, name='get_notifications_api'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/', views.all_notifications_view, name='all_notifications'), # NEW: Dedicated notifications page

    # URL for user profile editing
    path('profile/edit/', views.profile_update_view, name='profile_edit'),


    # URL for global search
    path('search/', views.global_search_view, name='global_search'),

    # URL for the Contact Us page
    path('contact/', views.contact_view, name='contact'),
    # URL for About Us page
    path('about/', views.about_view, name='about'),

    # Password Reset URLs
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='yoga_app/registration/password_reset_form.html',
             email_template_name='yoga_app/registration/password_reset_email.html',
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

    # Account Deletion URL
    path('account/delete/', views.delete_account_view, name='delete_account'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),

    # URL for submitting course reviews
    path('courses/<int:course_id>/review/submit/', views.submit_course_review_view, name='submit_course_review'),

    
    # NEW: Blog URLs
    path('blog/', views.blog_list_view, name='blog_list'),
    path('blog/<slug:post_slug>/', views.blog_detail_view, name='blog_detail'),
    path('blog/<slug:post_slug>/comment/', views.add_blog_comment_view, name='add_blog_comment'),
    path('blog/<slug:post_slug>/like/', views.toggle_blog_post_like, name='toggle_blog_post_like'), # NEW: URL for liking blog posts

    # NEW: Consultant URLs
    path('consultants/', views.consultant_list_view, name='consultant_list'),
    path('consultants/<int:consultant_id>/', views.consultant_detail_view, name='consultant_detail'),

    # NEW: Report Request URL
    path('request-report/', views.request_report_view, name='request_report'),
]