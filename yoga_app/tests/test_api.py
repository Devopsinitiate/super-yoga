import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from yoga_app.models import Course, YogaPose, BlogPost, BlogPostCategory, UserProfile


@pytest.mark.api
class TestCourseAPI:
    def test_list_courses(self, api_client, course):
        response = api_client.get('/api/v1/courses/')
        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_retrieve_course(self, api_client, course):
        response = api_client.get(f'/api/v1/courses/{course.id}/')
        assert response.status_code == 200
        assert response.data['title'] == course.title

    def test_list_courses_search(self, api_client, course):
        response = api_client.get('/api/v1/courses/', {'search': 'Yoga'})
        assert response.status_code == 200

    def test_list_courses_filter_free(self, api_client, free_course):
        response = api_client.get('/api/v1/courses/', {'price_filter': 'free'})
        assert response.status_code == 200
        assert all(c['is_free'] for c in response.data['results'])

    def test_list_courses_ordering(self, api_client, course):
        response = api_client.get('/api/v1/courses/', {'ordering': 'price'})
        assert response.status_code == 200

    def test_course_progress_unauthenticated(self, api_client, course):
        response = api_client.get(f'/api/v1/courses/{course.id}/progress/')
        assert response.status_code == 401 or response.status_code == 403

    def test_course_progress_authenticated(self, api_client_authenticated, enrolled_course):
        response = api_client_authenticated.get(f'/api/v1/courses/{enrolled_course.id}/progress/')
        assert response.status_code == 200
        assert 'total' in response.data


@pytest.mark.api
class TestYogaPoseAPI:
    def test_list_poses(self, api_client, yoga_pose):
        response = api_client.get('/api/v1/poses/')
        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_retrieve_pose(self, api_client, yoga_pose):
        response = api_client.get(f'/api/v1/poses/{yoga_pose.id}/')
        assert response.status_code == 200
        assert response.data['name'] == yoga_pose.name

    def test_filter_poses_by_difficulty(self, api_client, yoga_pose):
        response = api_client.get('/api/v1/poses/', {'difficulty': 'Beginner'})
        assert response.status_code == 200

    def test_search_poses(self, api_client, yoga_pose):
        response = api_client.get('/api/v1/poses/', {'search': 'Downward'})
        assert response.status_code == 200


@pytest.mark.api
class TestBreathingTechniqueAPI:
    def test_list_techniques(self, api_client, breathing_technique):
        response = api_client.get('/api/v1/breathing/')
        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_search_techniques(self, api_client, breathing_technique):
        response = api_client.get('/api/v1/breathing/', {'search': 'Alternate'})
        assert response.status_code == 200


@pytest.mark.api
class TestBlogPostAPI:
    def test_list_blog_posts(self, api_client, blog_post):
        response = api_client.get('/api/v1/blog/')
        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_retrieve_blog_post(self, api_client, blog_post):
        response = api_client.get(f'/api/v1/blog/{blog_post.id}/')
        assert response.status_code == 200
        assert response.data['title'] == blog_post.title

    def test_filter_blog_by_category(self, api_client, blog_post, blog_category):
        response = api_client.get('/api/v1/blog/', {'category_slug': blog_category.slug})
        assert response.status_code == 200

    def test_filter_blog_by_tag(self, api_client, blog_post, tag):
        response = api_client.get('/api/v1/blog/', {'tag_slug': tag.slug})
        assert response.status_code == 200

    def test_like_blog_post_unauthenticated(self, api_client, blog_post):
        response = api_client.post(f'/api/v1/blog/{blog_post.id}/like/')
        assert response.status_code == 401 or response.status_code == 403

    def test_like_blog_post_authenticated(self, api_client_authenticated, blog_post):
        response = api_client_authenticated.post(f'/api/v1/blog/{blog_post.id}/like/')
        assert response.status_code == 200
        assert 'liked' in response.data


@pytest.mark.api
class TestConsultantAPI:
    def test_list_consultants(self, api_client, consultant):
        response = api_client.get('/api/v1/consultants/')
        assert response.status_code == 200
        assert response.data['count'] >= 1


@pytest.mark.api
class TestNotificationAPI:
    def test_notifications_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/notifications/')
        assert response.status_code == 401

    def test_mark_all_read_unauthenticated(self, api_client):
        response = api_client.post('/api/v1/notifications/mark_all_read/')
        assert response.status_code == 401

    def test_notifications_authenticated(self, api_client_authenticated, notification):
        response = api_client_authenticated.get('/api/v1/notifications/')
        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_mark_all_read(self, api_client_authenticated, notification):
        response = api_client_authenticated.post('/api/v1/notifications/mark_all_read/')
        assert response.status_code == 200


@pytest.mark.api
class TestUserProfileAPI:
    def test_profile_unauthenticated(self, api_client):
        response = api_client.get('/api/v1/profile/')
        assert response.status_code == 401 or response.status_code == 403

    def test_profile_authenticated(self, api_client_authenticated, user_profile):
        response = api_client_authenticated.get('/api/v1/profile/')
        assert response.status_code == 200

    def test_profile_dashboard(self, api_client_authenticated):
        response = api_client_authenticated.get('/api/v1/profile/dashboard/')
        assert response.status_code == 200

    def test_profile_progress(self, api_client_authenticated):
        response = api_client_authenticated.get('/api/v1/profile/progress/')
        assert response.status_code == 200


@pytest.mark.api
class TestSearchAPI:
    def test_global_search(self, api_client, yoga_pose):
        response = api_client.get('/api/v1/search/global/', {'q': 'yoga'})
        assert response.status_code == 200
        assert 'poses' in response.data

    def test_suggestions(self, api_client, yoga_pose):
        response = api_client.get('/api/v1/search/suggestions/', {'q': 'Down'})
        assert response.status_code == 200
        assert 'suggestions' in response.data

    def test_suggestions_empty(self, api_client):
        response = api_client.get('/api/v1/search/suggestions/', {'q': ''})
        assert response.status_code == 200
        assert response.data['suggestions'] == []


@pytest.mark.api
class TestTestimonialAPI:
    def test_list_testimonials(self, api_client, testimonial):
        response = api_client.get('/api/v1/testimonials/')
        assert response.status_code == 200
        assert response.data['count'] >= 1


@pytest.mark.api
class TestBookingAPI:
    def test_create_booking(self, api_client):
        response = api_client.post('/api/v1/bookings/', {
            'full_name': 'API User',
            'email': 'api@example.com',
            'preferred_date': '2026-05-01',
            'preferred_time': 'Morning (8am-12pm)',
        })
        assert response.status_code == 201


@pytest.mark.api
class TestContactMessageAPI:
    def test_create_contact_message(self, api_client):
        response = api_client.post('/api/v1/contact/', {
            'name': 'API User',
            'email': 'api@example.com',
            'message': 'Test message via API',
        })
        assert response.status_code == 201


@pytest.mark.api
class TestAuthAPI:
    def test_token_obtain(self, api_client, user):
        response = api_client.post('/api/v1/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_token_obtain_invalid_credentials(self, api_client):
        response = api_client.post('/api/v1/auth/token/', {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_token_refresh(self, api_client, user):
        response = api_client.post('/api/v1/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        refresh_token = response.data['refresh']
        response = api_client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh_token,
        })
        assert response.status_code == 200
        assert 'access' in response.data
