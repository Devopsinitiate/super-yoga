import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from yoga_app.models import (
    UserProfile, Course, Module, Lesson, YogaPose, BreathingTechnique,
    BlogPost, BlogPostCategory, Tag, Consultant, Testimonial,
    CourseReview, DiscussionTopic, DiscussionPost, Notification,
    LessonComment, BlogComment, Payment, Booking, ContactMessage,
    UserLessonCompletion, UserCourseCompletion, NewsletterSubscription
)


@pytest.mark.model
class TestUserProfile:
    def test_profile_creation(self, user):
        profile, created = UserProfile.objects.get_or_create(user=user)
        assert profile.user == user
        assert str(profile) == f"{user.username}'s Profile"

    def test_profile_is_complete_property(self, user):
        profile = UserProfile.objects.get(user=user)
        assert profile.is_profile_complete is False

    def test_profile_signal_creates_on_user_creation(self, django_user_model):
        user = django_user_model.objects.create_user(
            username='signaluser',
            email='signal@example.com',
            password='testpass123'
        )
        assert hasattr(user, 'profile')

    def test_profile_enrolled_courses(self, user, course):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.enrolled_courses.add(course)
        assert profile.enrolled_courses.filter(id=course.id).exists()


@pytest.mark.model
class TestCourse:
    def test_course_creation(self, course):
        assert course.title == 'Test Yoga Course'
        assert course.price == 29.99
        assert course.is_free is False
        assert str(course) == 'Test Yoga Course'

    def test_free_course_auto_sets_is_free(self):
        course = Course.objects.create(
            title='Free Course',
            description='Free',
            instructor_name='Test',
            price=0.00,
            duration='1 week',
        )
        assert course.is_free is True

    def test_course_lessons_property(self, course, module, lesson):
        lessons = course.lessons
        assert lessons.count() == 1
        assert lessons.first() == lesson

    def test_course_str(self, course):
        assert str(course) == course.title


@pytest.mark.model
class TestModule:
    def test_module_creation(self, module):
        assert module.title == 'Module 1: Foundations'
        assert module.order == 1
        assert str(module) == f"Test Yoga Course - Module 1: {module.title}"

    def test_module_unique_order_per_course(self, course):
        Module.objects.create(course=course, title='Module 2', order=2)
        with pytest.raises(Exception):
            Module.objects.create(course=course, title='Module Duplicate', order=2)


@pytest.mark.model
class TestLesson:
    def test_lesson_creation(self, lesson):
        assert lesson.title == 'Lesson 1.1: Introduction'
        assert lesson.order == 1
        assert lesson.is_preview is False

    def test_lesson_unique_order_per_module(self, module):
        Lesson.objects.create(module=module, title='Lesson 2', order=2)
        with pytest.raises(Exception):
            Lesson.objects.create(module=module, title='Lesson Duplicate', order=2)


@pytest.mark.model
class TestYogaPose:
    def test_pose_creation(self, yoga_pose):
        assert yoga_pose.name == 'Downward Dog'
        assert yoga_pose.difficulty == 'Beginner'
        assert str(yoga_pose) == 'Downward Dog'

    def test_pose_difficulty_choices(self):
        choices = [c[0] for c in YogaPose.DIFFICULTY_CHOICES]
        assert 'Beginner' in choices
        assert 'Intermediate' in choices
        assert 'Advanced' in choices


@pytest.mark.model
class TestBreathingTechnique:
    def test_technique_creation(self, breathing_technique):
        assert breathing_technique.name == 'Alternate Nostril Breathing'
        assert str(breathing_technique) == 'Alternate Nostril Breathing'

    def test_technique_unique_name(self):
        BreathingTechnique.objects.create(
            name='Unique Technique',
            description='Test',
            instructions='Test',
        )
        with pytest.raises(Exception):
            BreathingTechnique.objects.create(
                name='Unique Technique',
                description='Test',
                instructions='Test',
            )


@pytest.mark.model
class TestBlogPost:
    def test_blog_post_creation(self, blog_post):
        assert blog_post.title == 'Test Blog Post'
        assert blog_post.is_published is True
        assert blog_post.published_date is not None
        assert str(blog_post) == 'Test Blog Post'

    def test_blog_post_slug_auto_generation(self, user, blog_category):
        post = BlogPost.objects.create(
            title='Auto Slug Post',
            author=user,
            category=blog_category,
            content='Content',
            is_published=True,
        )
        assert post.slug == 'auto-slug-post'

    def test_blog_post_tags(self, blog_post, tag):
        assert blog_post.tags.filter(id=tag.id).exists()

    def test_unpublished_post_no_published_date(self, user, blog_category):
        post = BlogPost.objects.create(
            title='Draft Post',
            slug='draft-post',
            author=user,
            category=blog_category,
            content='Draft content',
            is_published=False,
        )
        assert post.published_date is None


@pytest.mark.model
class TestCourseReview:
    def test_review_creation(self, user, course):
        review = CourseReview.objects.create(
            user=user,
            course=course,
            rating=5,
            comment='Great course!',
        )
        assert review.rating == 5
        assert str(review) == f"Review for {course.title} by {user.username} - 5 stars"

    def test_review_unique_per_user_course(self, user, course):
        CourseReview.objects.create(user=user, course=course, rating=4)
        with pytest.raises(Exception):
            CourseReview.objects.create(user=user, course=course, rating=5)

    def test_review_rating_validation(self, user, course):
        """Ratings outside 1-5 should raise ValidationError on full_clean()."""
        from django.core.exceptions import ValidationError
        review_low = CourseReview(user=user, course=course, rating=0)
        with pytest.raises(ValidationError):
            review_low.full_clean()

        second_user = User.objects.create_user('r3', 'r3@e.com', 'p')
        review_high = CourseReview(user=second_user, course=course, rating=6)
        with pytest.raises(ValidationError):
            review_high.full_clean()


@pytest.mark.model
class TestDiscussionTopic:
    def test_topic_creation(self, discussion_topic):
        assert discussion_topic.title == 'Test Discussion Topic'
        assert str(discussion_topic).startswith("Topic: 'Test Discussion Topic'")

    def test_topic_likes(self, discussion_topic, user, second_user):
        discussion_topic.likes.add(user, second_user)
        assert discussion_topic.likes.count() == 2


@pytest.mark.model
class TestDiscussionPost:
    def test_post_creation(self, discussion_post):
        assert discussion_post.content == 'Post content here'
        assert discussion_post.parent_post is None

    def test_post_replies(self, discussion_topic, user):
        parent = DiscussionPost.objects.create(
            topic=discussion_topic, user=user, content='Parent post'
        )
        reply = DiscussionPost.objects.create(
            topic=discussion_topic, user=user, content='Reply', parent_post=parent
        )
        assert parent.replies.filter(id=reply.id).exists()


@pytest.mark.model
class TestNotification:
    def test_notification_creation(self, notification):
        assert notification.notification_type == 'reply'
        assert notification.read is False
        assert notification.recipient is not None

    def test_notification_types(self):
        types = [t[0] for t in Notification.NOTIFICATION_TYPES]
        assert 'reply' in types
        assert 'like' in types
        assert 'blog_comment' in types


@pytest.mark.model
class TestPayment:
    def test_payment_creation(self, payment):
        assert payment.amount == 29.99
        assert payment.status == 'success'
        assert payment.reference == 'test-ref-123'

    def test_payment_status_choices(self):
        statuses = [s[0] for s in Payment.STATUS_CHOICES]
        assert 'pending' in statuses
        assert 'success' in statuses
        assert 'failed' in statuses

    def test_payment_reference_unique(self, user, course):
        Payment.objects.create(
            user=user, course=course, amount=10.00,
            reference='unique-ref', status='success'
        )
        with pytest.raises(Exception):
            Payment.objects.create(
                user=user, course=course, amount=10.00,
                reference='unique-ref', status='pending'
            )


@pytest.mark.model
class TestUserLessonCompletion:
    def test_completion_creation(self, user, lesson):
        completion = UserLessonCompletion.objects.create(user=user, lesson=lesson)
        assert completion.user == user
        assert completion.lesson == lesson
        assert str(completion) == f"{user.username} completed {lesson.title}"

    def test_completion_unique_per_user_lesson(self, user, lesson):
        UserLessonCompletion.objects.create(user=user, lesson=lesson)
        with pytest.raises(Exception):
            UserLessonCompletion.objects.create(user=user, lesson=lesson)


@pytest.mark.model
class TestUserCourseCompletion:
    def test_course_completion_creation(self, user, course):
        completion = UserCourseCompletion.objects.create(user=user, course=course)
        assert completion.user == user
        assert completion.course == course

    def test_course_completion_unique_per_user_course(self, user, course):
        UserCourseCompletion.objects.create(user=user, course=course)
        with pytest.raises(Exception):
            UserCourseCompletion.objects.create(user=user, course=course)


@pytest.mark.model
class TestConsultant:
    def test_consultant_creation(self, consultant):
        assert consultant.name == 'Test Consultant'
        assert consultant.is_available is True
        assert str(consultant) == 'Test Consultant'


@pytest.mark.model
class TestTestimonial:
    def test_testimonial_creation(self, testimonial):
        assert testimonial.author_name == 'Test Author'
        assert testimonial.rating == 5
        assert testimonial.is_approved is True

    def test_testimonial_default_not_approved(self):
        t = Testimonial.objects.create(
            author_name='New Author',
            feedback_text='Feedback',
        )
        assert t.is_approved is False


@pytest.mark.model
class TestBooking:
    def test_booking_creation(self, booking):
        assert booking.full_name == 'Test User'
        assert booking.preferred_time == 'Morning (8am-12pm)'

    def test_booking_time_choices(self):
        choices = [c[0] for c in Booking.TIME_CHOICES]
        assert 'Morning (8am-12pm)' in choices
        assert 'Afternoon (12pm-4pm)' in choices
        assert 'Evening (4pm-8pm)' in choices


@pytest.mark.model
class TestContactMessage:
    def test_contact_message_creation(self, contact_message):
        assert contact_message.name == 'Test Sender'
        assert contact_message.is_read is False


@pytest.mark.model
class TestNewsletterSubscription:
    def test_subscription_creation(self):
        sub = NewsletterSubscription.objects.create(email='sub@example.com')
        assert sub.email == 'sub@example.com'
        assert sub.is_active is True
        assert str(sub) == 'sub@example.com'

    def test_subscription_email_unique(self):
        NewsletterSubscription.objects.create(email='unique@example.com')
        with pytest.raises(Exception):
            NewsletterSubscription.objects.create(email='unique@example.com')


@pytest.mark.model
class TestBlogComment:
    def test_comment_creation(self, user, blog_post):
        comment = BlogComment.objects.create(
            post=blog_post, user=user, content='Great post!'
        )
        assert comment.content == 'Great post!'
        assert str(comment).startswith(f"Comment by {user.username}")


@pytest.mark.model
class TestLessonComment:
    def test_lesson_comment_creation(self, user, lesson):
        comment = LessonComment.objects.create(
            lesson=lesson, user=user, content='Helpful lesson!'
        )
        assert comment.content == 'Helpful lesson!'
