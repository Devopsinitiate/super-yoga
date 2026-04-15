"""
View-level tests using Django's test Client.
Covers URL routing, auth redirects, form submissions, and template rendering.
"""
import pytest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth.models import User
from yoga_app.models import Course, YogaPose, UserProfile, CourseReview, Payment
from yoga_app.tasks import send_newsletter_email


# ─── Home & Static Pages ──────────────────────────────────────────────────────

@pytest.mark.view
class TestPublicPages:
    def test_home_page_loads(self, client):
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_about_page_loads(self, client):
        response = client.get(reverse('about'))
        assert response.status_code == 200

    def test_contact_page_loads(self, client):
        response = client.get(reverse('contact'))
        assert response.status_code == 200

    def test_booking_page_loads(self, client):
        response = client.get(reverse('booking'))
        assert response.status_code == 200

    def test_health_check(self, client):
        response = client.get('/health/')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}


# ─── Auth Views ───────────────────────────────────────────────────────────────

@pytest.mark.view
class TestAuthViews:
    def test_register_page_loads(self, client):
        response = client.get(reverse('register'))
        assert response.status_code == 200

    def test_login_page_loads(self, client):
        response = client.get(reverse('login'))
        assert response.status_code == 200

    def test_register_creates_user(self, client):
        response = client.post(reverse('register'), {
            'username': 'newviewuser',
            'email': 'newviewuser@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
        })
        assert response.status_code == 302
        assert User.objects.filter(username='newviewuser').exists()

    def test_login_valid_credentials(self, client, user):
        # User must be active to log in
        user.is_active = True
        user.save()
        response = client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        assert response.status_code == 302

    def test_login_invalid_credentials(self, client):
        response = client.post(reverse('login'), {
            'username': 'nobody',
            'password': 'wrongpass',
        })
        assert response.status_code == 200  # re-renders form

    def test_dashboard_requires_login(self, client):
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert '/login' in response['Location'] or 'login' in response['Location']

    def test_profile_edit_requires_login(self, client):
        response = client.get(reverse('profile_edit'))
        assert response.status_code == 302


# ─── Course Views ─────────────────────────────────────────────────────────────

@pytest.mark.view
class TestCourseViews:
    def test_course_list_loads(self, client, course):
        response = client.get(reverse('courses'))
        assert response.status_code == 200

    def test_course_detail_loads(self, client, course):
        response = client.get(reverse('course_detail', args=[course.id]))
        assert response.status_code == 200

    def test_course_detail_404_on_missing(self, client):
        response = client.get(reverse('course_detail', args=[99999]))
        assert response.status_code == 404

    def test_course_content_requires_login(self, client, course, module, lesson):
        response = client.get(reverse('course_content', args=[course.id, lesson.id]))
        assert response.status_code == 302

    def test_course_content_requires_enrollment(self, client, user, course, module, lesson):
        user.is_active = True
        user.save()
        client.force_login(user)
        response = client.get(reverse('course_content', args=[course.id, lesson.id]))
        assert response.status_code == 302  # redirects to course_detail

    def test_enroll_free_course_requires_login(self, client, free_course):
        response = client.post(reverse('enroll_free_course', args=[free_course.id]))
        assert response.status_code == 302
        assert 'login' in response['Location']

    def test_enroll_free_course_authenticated(self, client, user, free_course):
        user.is_active = True
        user.save()
        client.force_login(user)
        response = client.post(reverse('enroll_free_course', args=[free_course.id]))
        assert response.status_code == 302
        profile = UserProfile.objects.get(user=user)
        assert profile.enrolled_courses.filter(id=free_course.id).exists()

    def test_submit_review_requires_enrollment(self, client, user, course):
        user.is_active = True
        user.save()
        client.force_login(user)
        response = client.post(reverse('submit_course_review', args=[course.id]), {
            'rating': 5,
            'comment': 'Great!',
        })
        assert response.status_code == 302  # redirects away — not enrolled


# ─── Content Views ────────────────────────────────────────────────────────────

@pytest.mark.view
class TestContentViews:
    def test_pose_list_loads(self, client, yoga_pose):
        response = client.get(reverse('poses'))
        assert response.status_code == 200

    def test_pose_detail_loads(self, client, yoga_pose):
        response = client.get(reverse('pose_detail', args=[yoga_pose.id]))
        assert response.status_code == 200

    def test_pose_detail_404(self, client):
        response = client.get(reverse('pose_detail', args=[99999]))
        assert response.status_code == 404

    def test_breathing_list_loads(self, client, breathing_technique):
        response = client.get(reverse('breathing'))
        assert response.status_code == 200

    def test_breathing_detail_loads(self, client, breathing_technique):
        response = client.get(reverse('breathing_technique_detail', args=[breathing_technique.id]))
        assert response.status_code == 200


# ─── Blog Views ───────────────────────────────────────────────────────────────

@pytest.mark.view
class TestBlogViews:
    def test_blog_list_loads(self, client, blog_post):
        response = client.get(reverse('blog_list'))
        assert response.status_code == 200

    def test_blog_detail_loads(self, client, blog_post):
        response = client.get(reverse('blog_detail', args=[blog_post.slug]))
        assert response.status_code == 200

    def test_blog_detail_404(self, client):
        response = client.get(reverse('blog_detail', args=['nonexistent-slug']))
        assert response.status_code == 404

    def test_blog_like_requires_login(self, client, blog_post):
        response = client.post(reverse('toggle_blog_post_like', args=[blog_post.slug]))
        assert response.status_code == 302

    def test_blog_like_authenticated(self, client, user, blog_post):
        user.is_active = True
        user.save()
        client.force_login(user)
        response = client.post(reverse('toggle_blog_post_like', args=[blog_post.slug]))
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['liked'] is True


# ─── Payment Flow Integration ─────────────────────────────────────────────────

@pytest.mark.view
@pytest.mark.integration
class TestPaymentFlow:
    def test_initiate_payment_requires_login(self, client, course):
        response = client.post(reverse('initiate_payment', args=[course.id]))
        assert response.status_code == 302
        assert 'login' in response['Location']

    def test_initiate_payment_authenticated(self, client, user, course):
        user.is_active = True
        user.save()
        client.force_login(user)
        response = client.post(reverse('initiate_payment', args=[course.id]))
        assert response.status_code == 200
        assert Payment.objects.filter(user=user, course=course, status='pending').exists()

    @patch('yoga_app.services.payment_service.requests.get')
    def test_verify_payment_success(self, mock_get, client, user, course):
        user.is_active = True
        user.save()
        client.force_login(user)

        payment = Payment.objects.create(
            user=user, course=course,
            amount=course.price, reference='test-verify-ref', status='pending'
        )

        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {
            'status': True,
            'data': {
                'status': 'success',
                'reference': 'test-verify-ref',
                'amount': int(course.price * 100),
                'customer': {'email': user.email},
                'metadata': {
                    'course_id': course.id,
                    'user_id': user.id,
                    'our_reference': 'test-verify-ref',
                },
            }
        }

        response = client.get(reverse('verify_payment') + '?reference=test-verify-ref')
        assert response.status_code == 302
        payment.refresh_from_db()
        assert payment.status == 'success'
        profile = UserProfile.objects.get(user=user)
        assert profile.enrolled_courses.filter(id=course.id).exists()

    @patch('yoga_app.services.payment_service.requests.get')
    def test_verify_payment_failure(self, mock_get, client, user, course):
        user.is_active = True
        user.save()
        client.force_login(user)

        Payment.objects.create(
            user=user, course=course,
            amount=course.price, reference='fail-ref', status='pending'
        )

        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {
            'status': True,
            'data': {
                'status': 'failed',
                'reference': 'fail-ref',
                'gateway_response': 'Declined',
            }
        }

        response = client.get(reverse('verify_payment') + '?reference=fail-ref')
        assert response.status_code == 302


# ─── Celery Tasks ─────────────────────────────────────────────────────────────

@pytest.mark.view
class TestCeleryTasks:
    @patch('yoga_app.tasks.send_mail')
    def test_send_newsletter_email(self, mock_send_mail):
        send_newsletter_email('Subject', 'Body', ['to@example.com'])
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        assert call_args[0][0] == 'Subject'
        assert 'to@example.com' in call_args[0][3]
