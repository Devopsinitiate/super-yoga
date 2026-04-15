import pytest
from django.contrib.auth.models import User
from yoga_app.models import (
    UserProfile, Course, Lesson, UserLessonCompletion, UserCourseCompletion,
    Notification, DiscussionTopic, DiscussionPost, BlogPost, BlogComment, Payment,
    CourseReview
)
from yoga_app.services import (
    EnrollmentService, PaymentService, NotificationService,
    ProgressService, SearchService, BlogService, DiscussionService, ReviewService
)


@pytest.mark.service
class TestEnrollmentService:
    def test_is_enrolled_true(self, user, course):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.enrolled_courses.add(course)
        assert EnrollmentService.is_enrolled(user, course) is True

    def test_is_enrolled_false(self, user, course):
        assert EnrollmentService.is_enrolled(user, course) is False

    def test_is_enrolled_anonymous_user(self, course):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        assert EnrollmentService.is_enrolled(anon, course) is False

    def test_enroll_user(self, user, course):
        success, status = EnrollmentService.enroll_user(user, course)
        assert success is True
        assert status == 'enrolled'
        assert EnrollmentService.is_enrolled(user, course) is True

    def test_enroll_user_already_enrolled(self, user, course):
        EnrollmentService.enroll_user(user, course)
        success, status = EnrollmentService.enroll_user(user, course)
        assert success is False
        assert status == 'already_enrolled'

    def test_enroll_free_course(self, user, free_course):
        success, status = EnrollmentService.enroll_free_course(user, free_course)
        assert success is True
        assert Payment.objects.filter(user=user, course=free_course, status='success').exists()

    def test_enroll_free_course_not_free(self, user, course):
        success, status = EnrollmentService.enroll_free_course(user, course)
        assert success is False
        assert status == 'not_free'

    def test_mark_lesson_complete(self, user, lesson):
        success, status = EnrollmentService.mark_lesson_complete(user, lesson)
        assert success is True
        assert status == 'completed'
        assert UserLessonCompletion.objects.filter(user=user, lesson=lesson).exists()

    def test_mark_lesson_complete_already_done(self, user, lesson):
        EnrollmentService.mark_lesson_complete(user, lesson)
        success, status = EnrollmentService.mark_lesson_complete(user, lesson)
        assert success is False
        assert status == 'already_complete'

    def test_mark_course_complete(self, user, course, module, lesson):
        EnrollmentService.mark_lesson_complete(user, lesson)
        success, status = EnrollmentService.mark_course_complete(user, course)
        assert success is True
        assert status == 'completed'

    def test_mark_course_complete_incomplete_lessons(self, user, course, module):
        Lesson.objects.create(module=module, title='Lesson 1', content='c1', order=1)
        Lesson.objects.create(module=module, title='Lesson 2', content='c2', order=2)
        success, status = EnrollmentService.mark_course_complete(user, course)
        assert success is False
        assert status == 'lessons_incomplete'

    def test_update_last_viewed_lesson(self, user, lesson):
        EnrollmentService.update_last_viewed_lesson(user, lesson)
        profile = UserProfile.objects.get(user=user)
        assert profile.last_viewed_lesson == lesson


@pytest.mark.service
class TestProgressService:
    def test_get_course_progress_empty(self, user, course):
        progress = ProgressService.get_course_progress(user, course)
        assert progress['total'] == 0
        assert progress['percentage'] == 0
        assert progress['is_complete'] is False

    def test_get_course_progress_partial(self, user, course, module):
        l1 = Lesson.objects.create(module=module, title='L1', content='c', order=1)
        l2 = Lesson.objects.create(module=module, title='L2', content='c', order=2)
        EnrollmentService.mark_lesson_complete(user, l1)
        progress = ProgressService.get_course_progress(user, course)
        assert progress['total'] == 2
        assert progress['completed'] == 1
        assert progress['percentage'] == 50

    def test_get_course_progress_full(self, user, course, module):
        l1 = Lesson.objects.create(module=module, title='L1', content='c', order=1)
        l2 = Lesson.objects.create(module=module, title='L2', content='c', order=2)
        EnrollmentService.mark_lesson_complete(user, l1)
        EnrollmentService.mark_lesson_complete(user, l2)
        progress = ProgressService.get_course_progress(user, course)
        assert progress['percentage'] == 100

    def test_get_completed_lesson_ids(self, user, course, module):
        l1 = Lesson.objects.create(module=module, title='L1', content='c', order=1)
        l2 = Lesson.objects.create(module=module, title='L2', content='c', order=2)
        EnrollmentService.mark_lesson_complete(user, l1)
        ids = ProgressService.get_completed_lesson_ids(user, course)
        assert l1.id in ids
        assert l2.id not in ids

    def test_get_user_dashboard_data(self, user, course, module, lesson):
        EnrollmentService.enroll_user(user, course)
        EnrollmentService.mark_lesson_complete(user, lesson)
        data = ProgressService.get_user_dashboard_data(user)
        assert len(data['enrolled_courses_data']) == 1
        assert data['enrolled_courses_data'][0]['course'] == course
        assert data['completed_courses_count'] == 0


@pytest.mark.service
class TestNotificationService:
    def test_create_notification(self, user, second_user):
        notif = NotificationService.create_notification(
            recipient=user, notification_type='like',
            message='Test message', sender=second_user, link='/test/'
        )
        assert notif.recipient == user
        assert notif.notification_type == 'like'

    def test_notify_reply(self, user, second_user, course):
        topic = DiscussionTopic.objects.create(
            course=course, user=user, title='Topic', content='Content'
        )
        notif = NotificationService.notify_reply(user, second_user, topic)
        assert notif is not None
        assert notif.recipient == user
        assert notif.sender == second_user

    def test_notify_reply_same_user(self, user, course):
        topic = DiscussionTopic.objects.create(
            course=course, user=user, title='Topic', content='Content'
        )
        notif = NotificationService.notify_reply(user, user, topic)
        assert notif is None

    def test_notify_like(self, user, second_user, course):
        topic = DiscussionTopic.objects.create(
            course=course, user=user, title='Topic', content='Content'
        )
        notif = NotificationService.notify_like(user, second_user, 'topic', topic)
        assert notif is not None
        assert notif.recipient == user

    def test_notify_blog_comment(self, user, second_user, blog_post):
        notif = NotificationService.notify_blog_comment(user, second_user, blog_post)
        assert notif is not None
        assert notif.recipient == user

    def test_get_user_notifications(self, user, second_user):
        NotificationService.create_notification(user, 'like', 'msg1', second_user)
        NotificationService.create_notification(user, 'reply', 'msg2', second_user)
        notifs = NotificationService.get_user_notifications(user)
        assert notifs.count() == 2

    def test_get_notifications_for_api_marks_read(self, user, second_user):
        NotificationService.create_notification(user, 'like', 'msg1', second_user)
        data = NotificationService.get_notifications_for_api(user)
        assert len(data) == 1
        assert Notification.objects.filter(recipient=user, read=True).count() == 1

    def test_mark_as_read_single(self, user, second_user):
        notif = NotificationService.create_notification(user, 'like', 'msg', second_user)
        result = NotificationService.mark_as_read(user, notif.id)
        assert result is True
        notif.refresh_from_db()
        assert notif.read is True

    def test_mark_as_read_all(self, user, second_user):
        NotificationService.create_notification(user, 'like', 'msg1', second_user)
        NotificationService.create_notification(user, 'reply', 'msg2', second_user)
        result = NotificationService.mark_as_read(user)
        assert result is False
        assert Notification.objects.filter(recipient=user, read=False).count() == 0


@pytest.mark.service
class TestSearchService:
    def test_global_search_with_query(self, yoga_pose, breathing_technique, course):
        results = SearchService.global_search(query='yoga')
        assert len(results['yoga_poses']) >= 1
        assert len(results['breathing_techniques']) >= 0
        assert len(results['courses']) >= 1

    def test_global_search_empty_query(self, yoga_pose):
        results = SearchService.global_search(query='')
        assert results['yoga_poses'].count() >= 1

    def test_global_search_category_filter(self, yoga_pose, course):
        results = SearchService.global_search(query='', category_filter='poses')
        assert results['yoga_poses'].count() >= 1
        assert results['courses'].count() == 0

    def test_global_search_difficulty_filter(self, yoga_pose):
        results = SearchService.global_search(
            query='', pose_difficulty_filter='Beginner'
        )
        assert results['yoga_poses'].count() >= 1

    def test_global_search_price_filter(self, course, free_course):
        results = SearchService.global_search(query='', course_price_filter='free')
        assert all(c.price == 0.00 for c in results['courses'])

    def test_get_suggestions(self, yoga_pose, course):
        suggestions = SearchService.get_suggestions('Downward')
        assert len(suggestions) > 0
        assert suggestions[0]['type'] == 'pose'

    def test_get_suggestions_empty(self):
        suggestions = SearchService.get_suggestions('')
        assert suggestions == []

    def test_get_suggestions_no_match(self):
        suggestions = SearchService.get_suggestions('xyznonexistent123')
        assert suggestions == []


@pytest.mark.service
class TestBlogService:
    def test_get_blog_detail(self, blog_post):
        post, comments = BlogService.get_blog_detail(blog_post.slug)
        assert post == blog_post
        assert list(comments) == []

    def test_is_liked_by_user_true(self, user, blog_post):
        blog_post.likes.add(user)
        assert BlogService.is_liked_by_user(blog_post, user) is True

    def test_is_liked_by_user_false(self, user, blog_post):
        assert BlogService.is_liked_by_user(blog_post, user) is False

    def test_is_liked_by_user_anonymous(self, blog_post):
        assert BlogService.is_liked_by_user(blog_post, None) is False

    def test_get_recent_posts(self, user, blog_category, blog_post):
        BlogPost.objects.create(
            title='Second Post', slug='second-post', author=user,
            category=blog_category, content='Content', is_published=True
        )
        recent = BlogService.get_recent_posts()
        assert recent.count() >= 2

    def test_get_categories(self, blog_category):
        categories = BlogService.get_categories()
        assert categories.count() >= 1

    def test_get_tags(self, tag):
        tags = BlogService.get_tags()
        assert tags.count() >= 1


@pytest.mark.service
class TestDiscussionService:
    def test_get_topics_for_course(self, discussion_topic, course):
        topics = DiscussionService.get_topics_for_course(course, discussion_topic.user)
        assert topics.count() >= 1

    def test_create_topic(self, course, user):
        topic = DiscussionService.create_topic(
            course=course, user=user, title='New Topic', content='Content'
        )
        assert topic.title == 'New Topic'
        assert topic.user == user

    def test_get_topic_detail(self, discussion_topic, course):
        topic = DiscussionService.get_topic_detail(discussion_topic.id, course)
        assert topic == discussion_topic

    def test_create_post(self, discussion_topic, user):
        post = DiscussionService.create_post(
            topic=discussion_topic, user=user, content='New post'
        )
        assert post.content == 'New post'
        assert post.user == user

    def test_toggle_topic_like(self, discussion_topic, user):
        liked, count = DiscussionService.toggle_topic_like(discussion_topic, user)
        assert liked is True
        assert count == 1
        liked, count = DiscussionService.toggle_topic_like(discussion_topic, user)
        assert liked is False
        assert count == 0

    def test_toggle_post_like(self, user):
        topic = DiscussionTopic.objects.create(
            course=Course.objects.create(title='C', description='d', instructor_name='I', price=0, duration='1w'),
            user=user, title='T', content='c'
        )
        post = DiscussionPost.objects.create(topic=topic, user=user, content='p')
        liked, count = DiscussionService.toggle_post_like(post, user)
        assert liked is True
        assert count == 1


@pytest.mark.service
class TestReviewService:
    def test_get_course_reviews(self, user, course):
        CourseReview.objects.create(user=user, course=course, rating=4, comment='Good')
        reviews = ReviewService.get_course_reviews(course)
        assert reviews.count() == 1

    def test_get_review_stats(self, user, course):
        CourseReview.objects.create(user=user, course=course, rating=4)
        CourseReview.objects.create(user=User.objects.create_user('r2', 'r2@e.com', 'p'), course=course, rating=5)
        stats = ReviewService.get_review_stats(course)
        assert stats['total_reviews'] == 2
        assert stats['average_rating'] == 4.5

    def test_get_user_review(self, user, course):
        review = CourseReview.objects.create(user=user, course=course, rating=5)
        assert ReviewService.get_user_review(course, user) == review

    def test_submit_or_update_review_create(self, user, course):
        review, action = ReviewService.submit_or_update_review(course, user, 5, 'Great!')
        assert action == 'created'
        assert review.rating == 5

    def test_submit_or_update_review_update(self, user, course):
        ReviewService.submit_or_update_review(course, user, 4)
        review, action = ReviewService.submit_or_update_review(course, user, 5, 'Updated!')
        assert action == 'updated'
        assert review.rating == 5
        assert review.comment == 'Updated!'
