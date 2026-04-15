import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from yoga_app.models import Course, UserProfile, Notification, UserCourseCompletion, UserLessonCompletion
from yoga_app.services import (
    EnrollmentService, NotificationService, SearchService
)


@pytest.mark.integration
class TestEnrollmentFlow:
    def test_full_enrollment_flow(self, client, user, course):
        client.login(username='testuser', password='testpass123')
        success, status = EnrollmentService.enroll_user(user, course)
        assert success is True
        assert EnrollmentService.is_enrolled(user, course) is True


@pytest.mark.integration
class TestProgressTracking:
    def test_lesson_to_course_completion(self, user, course, module, lesson):
        EnrollmentService.mark_lesson_complete(user, lesson)
        success, status = EnrollmentService.mark_course_complete(user, course)
        assert success is True
        assert UserCourseCompletion.objects.filter(user=user, course=course).exists()


@pytest.mark.integration
class TestNotificationFlow:
    def test_notification_creation_and_marking(self, user, second_user):
        notif = NotificationService.create_notification(
            recipient=user, notification_type='like',
            message='Test', sender=second_user
        )
        assert notif.read is False
        NotificationService.mark_as_read(user, notif.id)
        notif.refresh_from_db()
        assert notif.read is True


@pytest.mark.integration
class TestSearchIntegration:
    def test_cross_content_search(self, yoga_pose, breathing_technique, course):
        results = SearchService.global_search(query='')
        assert results['yoga_poses'].count() >= 1
        assert results['breathing_techniques'].count() >= 1
        assert results['courses'].count() >= 1
