# yoga_app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save # Import post_save signal
from django.dispatch import receiver # Import receiver decorator
from django.utils import timezone # Import timezone for current timestamp
from django.core.validators import MinValueValidator, MaxValueValidator # Ensure these are imported if used in other fields
from django.utils.text import slugify # NEW: Import slugify for tag slugs

# NEW: Import RichTextField and RichTextUploadingField from ckeditor_5
from django_ckeditor_5.fields import CKEditor5Field 


# User Profile Model to extend Django's built-in User model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', help_text="The associated Django User account.")
    enrolled_courses = models.ManyToManyField('Course', blank=True, related_name='enrolled_users', help_text="Courses the user has successfully enrolled in.")
    # NEW FIELD: To track the last lesson the user viewed - Added db_index
    last_viewed_lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, null=True, blank=True, related_name='last_viewed_by', help_text="The last lesson this user viewed.", db_index=True)

    # NEW FIELDS FOR USER PROFILE ENHANCEMENTS
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, help_text="User's profile picture.")
    bio = models.TextField(blank=True, null=True, help_text="A short biography or 'about me' for the user.")
    date_of_birth = models.DateField(blank=True, null=True, help_text="User's date of birth.")
    phone_number = models.CharField(max_length=20, blank=True, help_text="User's contact phone number.")
    address = models.CharField(max_length=255, blank=True, help_text="User's physical address.")
    city = models.CharField(max_length=100, blank=True, help_text="User's city.")
    country = models.CharField(max_length=100, blank=True, help_text="User's country.")

    # Social Media Links (Optional)
    facebook_profile = models.URLField(max_length=200, blank=True, help_text="Link to user's Facebook profile.")
    twitter_profile = models.URLField(max_length=200, blank=True, help_text="Link to user's Twitter profile.")
    linkedin_profile = models.URLField(max_length=200, blank=True, help_text="Link to user's LinkedIn profile.")
    instagram_profile = models.URLField(max_length=200, blank=True, help_text="Link to user's Instagram profile.")

    # Notification Preferences (NEW)
    receive_email_notifications = models.BooleanField(default=True, help_text="Whether to receive notifications via email.")
    receive_app_notifications = models.BooleanField(default=True, help_text="Whether to receive in-app notifications.")

    # Timestamp for when the profile was created/updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        # Ordering by user's username by default
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username}'s Profile"

    # Property to check if the profile is complete
    @property
    def is_profile_complete(self):
        # Define what constitutes a "complete" profile
        required_fields = [self.profile_picture, self.bio, self.date_of_birth, self.phone_number, self.address, self.city, self.country]
        return all(field is not None and field != '' for field in required_fields)


# Signal to create or update UserProfile when User is created/updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Creates a UserProfile when a new User is created.
    Updates an existing UserProfile when a User is saved (if the profile exists).
    """
    if created:
        # Only create if the UserProfile doesn't already exist for this user
        UserProfile.objects.get_or_create(user=instance)
        print(f"DEBUG: UserProfile created for new user: {instance.username}")
    else:
        # If the user is being updated, ensure their profile is also saved if it exists
        # This handles cases where user.save() is called but profile fields might be updated elsewhere
        if hasattr(instance, 'profile'):
            instance.profile.save()
            print(f"DEBUG: UserProfile updated for existing user: {instance.username}")


# Model for Yoga Poses
class YogaPose(models.Model):
    """
    Represents a single yoga pose with its details.
    """
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    name = models.CharField(max_length=100, help_text="The common name of the yoga pose.", db_index=True) # Added db_index
    sanskrit_name = models.CharField(max_length=100, blank=True, null=True, help_text="The Sanskrit name of the pose.", db_index=True) # Added db_index
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner', help_text="The difficulty level of the pose.")
    description = CKEditor5Field(help_text="Detailed description of the pose, including benefits and instructions.")
    instructions = CKEditor5Field(help_text="Step-by-step instructions for performing the pose.")
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL for an image representing the pose (e.g., Unsplash link, placeholder).")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="Embed URL for a video demonstration (e.g., YouTube embed link)")
    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)

    class Meta:
        verbose_name = "Yoga Pose"
        verbose_name_plural = "Yoga Poses"
        ordering = ['name']


    def __str__(self):
        return self.name

# Model for Breathing Techniques (Pranayama)
class BreathingTechnique(models.Model):
    """
    Represents a breathing technique or pranayama.
    """
    name = models.CharField(max_length=100, unique=True, help_text="The common name of the breathing technique.", db_index=True) # Added db_index
    sanskrit_name = models.CharField(max_length=100, blank=True, null=True, help_text="The Sanskrit name of the technique.", db_index=True) # Added db_index
    description = CKEditor5Field(help_text="Detailed description of the technique, including benefits and instructions.")
    instructions = CKEditor5Field(help_text="Step-by-step instructions for performing the technique.")
    duration = models.CharField(max_length=50, blank=True, null=True, help_text="Recommended duration for practicing this technique (e.g., '5 minutes', '10 breaths').")
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL for an image representing the technique (e.g., Unsplash link, placeholder).")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="Embed URL for a video demonstration (e.g., YouTube embed link)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Breathing Technique"
        verbose_name_plural = "Breathing Techniques"
        ordering = ['name']


    def __str__(self):
        return self.name

# Model for Yoga Courses
class Course(models.Model):
    """
    Represents a yoga course offered by Yoga Kailasa.
    """
    title = models.CharField(max_length=200, help_text="Title of the yoga course.", db_index=True) # Added db_index
    description = CKEditor5Field(help_text="A detailed description of the course content (visible to all).")
    instructor_name = models.CharField(max_length=100, help_text="Name of the course instructor.")
    overview_content = CKEditor5Field(blank=True, null=True, help_text="General overview content for the course, separate from structured lessons.") 
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Price of the course. Use 0.00 for free courses.", db_index=True) # Added db_index
    duration = models.CharField(max_length=50, help_text="Duration of the course (e.g., '4 weeks', '8 weeks').")
    is_free = models.BooleanField(default=False, help_text="Indicates if the course is free.")
    includes = CKEditor5Field(blank=True, null=True, help_text="What the course includes (e.g., 'HD Videos', 'PDF Guides').")
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL for an image representing the course (e.g., Unsplash link, placeholder).")
    is_popular = models.BooleanField(default=False, help_text="Mark as true to highlight this course as popular.", db_index=True) # Added db_index
    start_date = models.DateField(blank=True, null=True, help_text="Optional start date for the course.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ['title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.is_free = (self.price == 0.00)
        super().save(*args, **kwargs)
    
    @property
    def lessons(self):
        """Returns all lessons associated with this course through its modules."""
        return Lesson.objects.filter(module__course=self).order_by('module__order', 'order')


# Model for Course Modules
class Module(models.Model):
    """
    Represents a module within a course.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', help_text="The course this module belongs to.")
    title = models.CharField(max_length=200, help_text="Title of the module (e.g., 'Module 1: Foundations of Yoga').")
    description = CKEditor5Field(blank=True, null=True, help_text="A brief description of the module's content.")
    order = models.PositiveIntegerField(default=0, help_text="The display order of the module within the course.", db_index=True) # Added db_index
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ['order']
        unique_together = ('course', 'order') # Ensure unique order within a course

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"

# Model for Lessons within Modules
class Lesson(models.Model):
    """
    Represents a lesson within a module.
    """
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', help_text="The module this lesson belongs to.")
    title = models.CharField(max_length=200, help_text="Title of the lesson (e.g., 'Lesson 1.1: Introduction to Asanas').")
    order = models.PositiveIntegerField(default=0, help_text="The display order of the lesson within the module.", db_index=True) # Added db_index
    content = CKEditor5Field(help_text="The detailed content of the lesson (can include HTML/Markdown).")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="Embed URL for a video (e.g., YouTube embed link).")
    duration_minutes = models.PositiveIntegerField(default=0, help_text="Approximate duration of the lesson in minutes.")
    # NEW FIELD: To track if a lesson is a preview (accessible without enrollment)
    is_preview = models.BooleanField(default=False, help_text="If true, this lesson can be viewed as a preview without course enrollment.")

    resources_content = CKEditor5Field(blank=True, null=True, help_text="Additional resources for this lesson (e.g., PDF links, external articles).")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ['module__order', 'order']
        unique_together = ('module', 'order') # Ensure unique order within a module

    def __str__(self):
        return f"{self.module.course.title} - {self.module.title} - Lesson {self.order}: {self.title}"

# Model to track user lesson completion
class UserLessonCompletion(models.Model):
    """
    Tracks when a specific user completes a specific lesson.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who completed the lesson.", db_index=True) # Added db_index
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, help_text="The lesson that was completed.", db_index=True) # Added db_index
    completed_at = models.DateTimeField(default=timezone.now, help_text="The timestamp when the lesson was marked as complete.")

    class Meta:
        verbose_name = "User Lesson Completion"
        verbose_name_plural = "User Lesson Completions"
        unique_together = ('user', 'lesson') # A user can complete a lesson only once
        ordering = ['completed_at']

    def __str__(self):
        return f"{self.user.username} completed {self.lesson.title}"


# NEW: Model for Discussion Topics within a Course
class DiscussionTopic(models.Model):
    """
    Represents a discussion topic or thread within a specific course.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussion_topics', help_text="The course this topic belongs to.", db_index=True) # Added db_index
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who created this topic.", db_index=True) # Added db_index
    title = models.CharField(max_length=255, help_text="Title of the discussion topic.")
    # Using CKEditor5Field for rich content and image uploads
    content = CKEditor5Field(help_text="The initial post content for the topic.")
    likes = models.ManyToManyField(User, related_name='liked_topics', blank=True, help_text="Users who liked this topic.") # NEW FIELD
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussion_topics', help_text="Optional: The specific lesson this topic relates to.", db_index=True) # Added db_index
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the topic was created.", db_index=True) # Added db_index
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the topic was last updated.")

    class Meta:
        ordering = ['-created_at'] # Order by most recent topics first
        verbose_name = "Discussion Topic"
        verbose_name_plural = "Discussion Topics"

    def __str__(self):
        return f"Topic: '{self.title}' in '{self.course.title}' by {self.user.username}"

# NEW: Model for Discussion Posts (replies) within a Discussion Topic
class DiscussionPost(models.Model):
    """
    Represents a reply or comment within a discussion topic.
    """
    topic = models.ForeignKey(DiscussionTopic, on_delete=models.CASCADE, related_name='posts', help_text="The discussion topic this post belongs to.", db_index=True) # Added db_index
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who created this post.", db_index=True) # Added db_index
    content = CKEditor5Field(help_text="The content of the discussion post.")
    parent_post = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', help_text="Optional: The parent post this is a reply to.")
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True, help_text="Users who liked this post.") # NEW FIELD
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the post was created.", db_index=True) # Added db_index
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the post was last updated.")

    class Meta:
        ordering = ['created_at'] # Order by oldest posts first within a topic
        verbose_name = "Discussion Post"
        verbose_name_plural = "Discussion Posts"

    def __str__(self):
        return f"Post by {self.user.username} on '{self.topic.title}' at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# Model to track user course completion (still relevant for overall course completion)
class UserCourseCompletion(models.Model):
    """
    Tracks when a specific user completes a specific course.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_completions', help_text="The user who completed the course.", db_index=True) # Added db_index
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_completions', help_text="The course that was completed.", db_index=True) # Added db_index
    completed_at = models.DateTimeField(default=timezone.now, help_text="The timestamp when the course was marked as complete.")

    class Meta:
        verbose_name = "User Course Completion"
        verbose_name_plural = "User Course Completions"
        unique_together = ('user', 'course')
        ordering = ['completed_at']

    def __str__(self):
        return f"{self.user.username} completed {self.course.title} on {self.completed_at.strftime('%Y-%m-%d')}"
    

# Model for Course Reviews
class CourseReview(models.Model):
    """
    Represents a review and rating for a specific course.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who submitted the review.", db_index=True) # Added db_index
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', help_text="The course being reviewed.", db_index=True) # Added db_index
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Rating given by the user (1 to 5 stars).", db_index=True) # Added db_index
    comment = models.TextField(blank=True, null=True, help_text="Optional text comment for the review.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the review was submitted.", db_index=True) # Added db_index
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensures a user can only submit one review per course
        verbose_name = "Course Review"
        verbose_name_plural = "Course Reviews"
        unique_together = ('course', 'user')
        ordering = ['-submitted_at'] # Order by most recent first

    def __str__(self):
        return f"Review for {self.course.title} by {self.user.username} - {self.rating} stars"


# Model for Consultants/Therapists
class Consultant(models.Model):
    """
    Represents a yoga consultant or therapist.
    """
    name = models.CharField(max_length=100, help_text="Name of the consultant.", db_index=True) # Added db_index
    specialty = models.CharField(max_length=200, help_text="Consultant's specialty (e.g., 'Yoga Therapist & Ayurveda Specialist').", db_index=True) # Added db_index
    bio = CKEditor5Field(help_text="A short biography of the consultant.")
    profile_picture_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL to the consultant's profile picture.") # Added back
    is_available = models.BooleanField(default=True, help_text="Indicates if the consultant is currently available for bookings.")
    contact_email = models.EmailField(blank=True, help_text="Consultant's contact email.")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Consultant's contact phone number.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Consultant"
        verbose_name_plural = "Consultants"
        ordering = ['name']

    def __str__(self):
        return self.name

# Testimonial Model (UPDATED: Added is_approved field)
class Testimonial(models.Model):
    author_name = models.CharField(max_length=100, help_text="Name of the person giving the testimonial.")
    email = models.EmailField(blank=True, null=True, help_text="Email of the person (optional, for internal contact).")
    feedback_text = models.TextField(help_text="The actual testimonial or feedback message.")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], blank=True, null=True, help_text="Optional rating from 1 to 5 stars.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the testimonial was submitted.")
    is_approved = models.BooleanField(default=False, help_text="Whether this testimonial has been approved for public display.") # NEW FIELD

    class Meta:
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Testimonial by {self.author_name} - {self.rating} stars"

# Model for Booking Private Sessions
class Booking(models.Model):
    """
    Records a booking for a private session.
    """
    TIME_CHOICES = [ # Preserving your TIME_CHOICES
        ('Morning (8am-12pm)', 'Morning (8am-12pm)'), # Corrected typo: 8pm -> 8am
        ('Afternoon (12pm-4pm)', 'Afternoon (12pm-4pm)'),
        ('Evening (4pm-8pm)', 'Evening (4pm-8pm)'),
    ]

    full_name = models.CharField(max_length=100, help_text="Full name of the person booking.")
    email = models.EmailField(help_text="Email address for communication regarding the booking.")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Optional phone number for contact.") # Added back
    preferred_date = models.DateField(help_text="Preferred date for the session.", db_index=True) # Added db_index
    preferred_time = models.CharField(
        max_length=50,
        choices=TIME_CHOICES,
        help_text="Preferred time slot for the session.",
        db_index=True # Added db_index
    )
    booked_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the booking was made.")
    message = models.TextField(blank=True, null=True, help_text="Any specific requests or questions for the session.")


    def __str__(self):
        return f"Booking by {self.full_name} on {self.preferred_date} ({self.preferred_time})"




# Model for Newsletter Subscriptions
class NewsletterSubscription(models.Model):
    """
    Records an email address for newsletter subscriptions.
    """
    email = models.EmailField(unique=True, help_text="Email address of the subscriber.")
    subscribed_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the subscription was made.")
    is_active = models.BooleanField(default=True, help_text="Indicates if the subscription is active.")
    class Meta:
        verbose_name = "Newsletter Subscription"
        verbose_name_plural = "Newsletter Subscriptions"
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email

# Model for Contact Message (General Feedback Form)
class ContactMessage(models.Model):
    """
    Records messages submitted through the general contact/feedback form.
    """
    name = models.CharField(max_length=100, help_text="Name of the sender.")
    email = models.EmailField(help_text="Email address of the sender.", db_index=True) # Added db_index
    subject = models.CharField(max_length=255, blank=True, null=True, help_text="Optional subject of the message.") # Added back
    message = models.TextField(help_text="The content of the message.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the message was submitted.", db_index=True) # Added db_index
    is_read = models.BooleanField(default=False, help_text="Indicates if the message has been read by an admin.")

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Message from {self.name} ({self.email}) - Subject: {self.subject[:50]}..."

# Model to track Course Payments
class Payment(models.Model):
    """
    Records a payment transaction for a course.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="The user who made this payment.", db_index=True) # Added db_index
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, help_text="The course associated with this payment.", db_index=True) # Added db_index
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid for the course.")
    reference = models.CharField(max_length=100, unique=True, help_text="Unique transaction reference from payment gateway.") # Unique implies index
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of the payment.", db_index=True) # Added db_index
    paid_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the payment was successfully made.", db_index=True) # Added db_index
    verified_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the payment was successfully verified.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the payment record was created in the system.", db_index=True) # Added db_index
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the payment record was last updated.") # Added back

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment for {self.course.title if self.course else 'N/A'} by {self.user.username if self.user else 'Guest'} - {self.reference} ({self.status})"


# NEW: Notification Model
class Notification(models.Model):
    """
    Represents a notification for a user.
    """
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', help_text="The user who receives the notification.", db_index=True) # Added db_index
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications', help_text="The user who triggered the notification (optional).", db_index=True) # Added db_index

    NOTIFICATION_TYPES = [
        ('reply', 'New Reply'),
        ('like', 'New Like'),
        ('course_update', 'Course Update'),
        ('admin_message', 'Admin Message'),
        ('blog_comment', 'Blog Comment'), # NEW
        ('blog_post_like', 'Blog Post Like'), # NEW
        ('new_blog_post', 'New Blog Post'), # NEW
    ]
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, help_text="Type of notification.", db_index=True)

    message = models.TextField(help_text="The content of the notification message.")
    link = models.URLField(max_length=500, blank=True, help_text="Optional URL to link to the relevant content.")
    read = models.BooleanField(default=False, help_text="Indicates if the notification has been read.", db_index=True) # Added db_index
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the notification was created.", db_index=True) # Added db_index
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the notification was last updated (e.g., marked read).")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at'] # Order by most recent first

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.notification_type} - {self.message[:50]}..."

# NEW: Lesson Comment Model
class LessonComment(models.Model):
    """
    Represents a comment made by a user on a specific lesson.
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments', help_text="The lesson this comment belongs to.", db_index=True) # Added db_index
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who posted the comment.", db_index=True) # Added db_index
    content = models.TextField(help_text="The content of the comment.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the comment was created.", db_index=True) # Added db_index
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the comment was last updated.")

    class Meta:
        ordering = ['created_at'] # Order by oldest comments first
        verbose_name = "Lesson Comment"
        verbose_name_plural = "Lesson Comments"

    def __str__(self):
        return f"Comment by {self.user.username} on {self.lesson.title[:50]}..."


# NEW: Blog Category Model
class BlogPostCategory(models.Model):
    """
    Represents a category for blog posts (e.g., Yoga Tips, Meditation, Healthy Recipes).
    """
    name = models.CharField(max_length=100, unique=True, help_text="Name of the blog category.")
    slug = models.SlugField(max_length=100, unique=True, help_text="A URL-friendly version of the category name.")
    description = models.TextField(blank=True, help_text="A brief description of the category.")

    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# NEW: Tag Model for Blog Posts
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="Name of the tag (e.g., 'Mindfulness', 'Nutrition').")
    slug = models.SlugField(max_length=50, unique=True, help_text="A unique slug for the tag URL.")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# NEW: Blog Post Model
class BlogPost(models.Model):
    """
    Represents a single blog post.
    """
    title = models.CharField(max_length=255, unique=True, help_text="Title of the blog post.")
    slug = models.SlugField(max_length=255, unique=True, help_text="A URL-friendly version of the post title.")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts', help_text="The user who authored this blog post.")
    category = models.ForeignKey(BlogPostCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts', help_text="The category this blog post belongs to.")
    tags = models.ManyToManyField('Tag', related_name='blog_posts', blank=True, help_text="Tags associated with this blog post.")
    excerpt = CKEditor5Field(blank=True, help_text="A short summary or excerpt of the blog post.")
    content = CKEditor5Field(help_text="Full content of the blog post.")
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True, help_text="An optional featured image for the blog post.")
    published_date = models.DateTimeField(null=True, blank=True, help_text="Date and time when the post was published.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the post was last updated.")
    is_published = models.BooleanField(default=False, help_text="Whether the blog post is publicly visible.")
    likes = models.ManyToManyField(User, related_name='liked_blog_posts', blank=True, help_text="Users who liked this blog post.")



    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-published_date'] # Order by most recent first

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and not self.published_date:
            self.published_date = timezone.now() # Set published_date only if it's being published for the first time
        super().save(*args, **kwargs)
    
    

    
# NEW: Blog Comment Model
class BlogComment(models.Model):
    """
    Represents a comment made by a user on a specific blog post.
    """
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments', help_text="The blog post this comment belongs to.")
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The user who posted the comment.")
    content = models.TextField(help_text="The content of the comment.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the comment was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the comment was last updated.")

    class Meta:
        verbose_name = "Blog Comment"
        verbose_name_plural = "Blog Comments"
        ordering = ['created_at'] # Order by oldest comments first

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title[:30]}..."

