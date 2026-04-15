import pytest
from django.contrib.auth.models import User
from yoga_app.models import (
    UserProfile, Course, Module, Lesson, YogaPose, BreathingTechnique,
    BlogPost, BlogPostCategory, Tag, Consultant, Testimonial,
    CourseReview, DiscussionTopic, DiscussionPost, Notification,
    LessonComment, BlogComment, Payment, Booking, ContactMessage,
    UserLessonCompletion, UserCourseCompletion, NewsletterSubscription
)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def user_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


@pytest.fixture
def second_user(django_user_model):
    return django_user_model.objects.create_user(
        username='seconduser',
        email='second@example.com',
        password='testpass123'
    )


@pytest.fixture
def course():
    return Course.objects.create(
        title='Test Yoga Course',
        description='A test course description',
        instructor_name='Test Instructor',
        price=29.99,
        duration='4 weeks',
        is_popular=True,
    )


@pytest.fixture
def free_course():
    return Course.objects.create(
        title='Free Yoga Course',
        description='A free course description',
        instructor_name='Test Instructor',
        price=0.00,
        duration='2 weeks',
        is_popular=False,
    )


@pytest.fixture
def module(course):
    return Module.objects.create(
        course=course,
        title='Module 1: Foundations',
        description='Introduction to yoga foundations',
        order=1,
    )


@pytest.fixture
def lesson(module):
    return Lesson.objects.create(
        module=module,
        title='Lesson 1.1: Introduction',
        content='Lesson content here',
        order=1,
        duration_minutes=30,
    )


@pytest.fixture
def yoga_pose():
    return YogaPose.objects.create(
        name='Downward Dog',
        sanskrit_name='Adho Mukha Svanasana',
        difficulty='Beginner',
        description='A foundational yoga pose',
        instructions='Step by step instructions',
    )


@pytest.fixture
def breathing_technique():
    return BreathingTechnique.objects.create(
        name='Alternate Nostril Breathing',
        sanskrit_name='Nadi Shodhana',
        description='A calming breathing technique',
        instructions='Step by step instructions',
        duration='5 minutes',
    )


@pytest.fixture
def blog_category():
    return BlogPostCategory.objects.create(
        name='Yoga Tips',
        slug='yoga-tips',
        description='Tips and tricks for yoga practice',
    )


@pytest.fixture
def tag():
    return Tag.objects.create(
        name='Mindfulness',
        slug='mindfulness',
    )


@pytest.fixture
def blog_post(user, blog_category, tag):
    post = BlogPost.objects.create(
        title='Test Blog Post',
        slug='test-blog-post',
        author=user,
        category=blog_category,
        excerpt='A short excerpt',
        content='Full blog post content',
        is_published=True,
    )
    post.tags.add(tag)
    return post


@pytest.fixture
def consultant():
    return Consultant.objects.create(
        name='Test Consultant',
        specialty='Yoga Therapy',
        bio='Experienced yoga therapist',
        is_available=True,
    )


@pytest.fixture
def testimonial():
    return Testimonial.objects.create(
        author_name='Test Author',
        email='author@example.com',
        feedback_text='Great experience!',
        rating=5,
        is_approved=True,
    )


@pytest.fixture
def enrolled_course(user, course):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.enrolled_courses.add(course)
    return course


@pytest.fixture
def discussion_topic(course, user):
    return DiscussionTopic.objects.create(
        course=course,
        user=user,
        title='Test Discussion Topic',
        content='Topic content here',
    )


@pytest.fixture
def discussion_post(discussion_topic, user):
    return DiscussionPost.objects.create(
        topic=discussion_topic,
        user=user,
        content='Post content here',
    )


@pytest.fixture
def notification(user, second_user):
    return Notification.objects.create(
        recipient=user,
        sender=second_user,
        notification_type='reply',
        message='Test notification message',
        link='/test/',
    )


@pytest.fixture
def payment(user, course):
    return Payment.objects.create(
        user=user,
        course=course,
        amount=29.99,
        reference='test-ref-123',
        status='success',
    )


@pytest.fixture
def booking():
    return Booking.objects.create(
        full_name='Test User',
        email='test@example.com',
        preferred_date='2026-05-01',
        preferred_time='Morning (8am-12pm)',
    )


@pytest.fixture
def contact_message():
    return ContactMessage.objects.create(
        name='Test Sender',
        email='sender@example.com',
        subject='Test Subject',
        message='Test message content',
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def api_client_authenticated(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
