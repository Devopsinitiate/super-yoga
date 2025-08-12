from django.test import TestCase
from django.urls import reverse
from .models import Course, YogaPose
from .forms import ContactMessageForm
from django.contrib.auth.models import User
from .tasks import send_newsletter_email
from unittest.mock import patch

# Create your tests here.

class CourseModelTest(TestCase):
    def test_course_str(self):
        course = Course.objects.create(title="Yoga 101", price=0)
        self.assertEqual(str(course), "Yoga 101")

class YogaPoseModelTest(TestCase):
    def test_pose_str(self):
        pose = YogaPose.objects.create(name="Downward Dog")
        self.assertEqual(str(pose), "Downward Dog")

class ContactFormTest(TestCase):
    def test_valid_form(self):
        form = ContactMessageForm(data={'name': 'Test', 'email': 'test@example.com', 'message': 'Hi'})
        self.assertTrue(form.is_valid())

class EnrollmentViewTest(TestCase):
    def test_enroll_redirects_for_anonymous(self):
        course = Course.objects.create(title="Test Course", price=0)
        response = self.client.post(reverse('initiate_payment', args=[course.id]))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

class RegistrationIntegrationTest(TestCase):
    def test_user_registration_and_login(self):
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after registration
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)
        login = self.client.login(username='testuser', password='Testpass123!')
        self.assertTrue(login)

class CourseEnrollmentIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='enrolluser', password='Testpass123!')
        self.course = Course.objects.create(title="Yoga 101", price=0)

    def test_enroll_course_authenticated(self):
        self.client.login(username='enrolluser', password='Testpass123!')
        response = self.client.post(reverse('initiate_payment', args=[self.course.id]))
        self.assertIn(response.status_code, [200, 302])  # Should succeed or redirect

class CeleryTaskTest(TestCase):
    @patch('yoga_app.tasks.send_mail')
    def test_send_newsletter_email_task(self, mock_send_mail):
        # Only test the synchronous call to avoid needing Redis
        send_newsletter_email('Subject', 'Body', ['to@example.com'])
        mock_send_mail.assert_called_once_with('Subject', 'Body', 'no-reply@yogakailasa.com', ['to@example.com'])

class PaymentVerificationIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='payuser', password='Testpass123!')
        self.course = Course.objects.create(title="Yoga 101", price=1000)
        self.client.login(username='payuser', password='Testpass123!')
        # Simulate a pending payment
        self.payment = self.course.payment_set.create(
            user=self.user,
            amount=1000,
            status='pending',
            reference='testref123',
        )

    def test_verify_payment_success(self):
        # Simulate Paystack callback with success
        response = self.client.get(reverse('verify_payment') + '?reference=testref123')
        self.assertIn(response.status_code, [200, 302])
        # Check for success message in response context or messages

class CommentSubmissionIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commentuser', password='Testpass123!')
        self.course = Course.objects.create(title="Yoga 101", price=0)
        self.client.login(username='commentuser', password='Testpass123!')
        # Ensure UserProfile exists for test user
        from .models import UserProfile
        UserProfile.objects.get_or_create(user=self.user)

    def test_submit_course_review(self):
        # Enroll user in course
        self.user.profile.enrolled_courses.add(self.course)
        response = self.client.post(reverse('submit_course_review', args=[self.course.id]), {
            'rating': 5,
            'comment': 'Great course!'
        })
        self.assertIn(response.status_code, [200, 302])
        # Check that review was created
        from .models import CourseReview
        review_exists = CourseReview.objects.filter(course=self.course, user=self.user).exists()
        self.assertTrue(review_exists)

    def test_submit_comment_invalid(self):
        # Try submitting without enrollment
        response = self.client.post(reverse('submit_course_review', args=[self.course.id]), {
            'rating': 5,
            'comment': 'Should fail!'
        })
        self.assertIn(response.status_code, [200, 302])
        # Should not create review
        from .models import CourseReview
        review_exists = CourseReview.objects.filter(course=self.course, user=self.user).exists()
        self.assertFalse(review_exists)
