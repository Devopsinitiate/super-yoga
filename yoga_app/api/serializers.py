from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from yoga_app.models import (
    UserProfile, Course, Module, Lesson, YogaPose, BreathingTechnique,
    BlogPost, BlogPostCategory, Tag, Consultant, Testimonial,
    CourseReview, DiscussionTopic, DiscussionPost, Notification,
    LessonComment, BlogComment, Payment, Booking, ContactMessage
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    enrolled_courses_count = serializers.SerializerMethodField()
    profile_completion = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'profile_picture', 'bio', 'date_of_birth',
            'phone_number', 'address', 'city', 'country',
            'facebook_profile', 'twitter_profile', 'linkedin_profile', 'instagram_profile',
            'receive_email_notifications', 'receive_app_notifications',
            'enrolled_courses_count', 'profile_completion',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_enrolled_courses_count(self, obj):
        return obj.enrolled_courses.count()

    def get_profile_completion(self, obj):
        required = [obj.profile_picture, obj.bio, obj.date_of_birth, obj.phone_number, obj.address, obj.city, obj.country]
        filled = sum(1 for field in required if field and field != '')
        return int((filled / len(required)) * 100)


class LessonSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'content', 'video_url', 'duration_minutes', 'is_preview', 'resources_content', 'is_completed']

    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.userlessoncompletion_set.filter(user=request.user).exists()
        return False


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'lessons']


class CourseReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CourseReview
        fields = ['id', 'user', 'rating', 'comment', 'submitted_at', 'updated_at']
        read_only_fields = ['submitted_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    reviews = CourseReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    total_lessons = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'instructor_name', 'overview_content',
            'price', 'duration', 'is_free', 'includes', 'image_url', 'is_popular',
            'start_date', 'modules', 'reviews', 'average_rating', 'review_count',
            'is_enrolled', 'total_lessons', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_average_rating(self, obj):
        return obj.reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile:
                return profile.enrolled_courses.filter(id=obj.id).exists()
        return False

    def get_total_lessons(self, obj):
        return obj.modules.aggregate(total=Count('lessons'))['total'] or 0


class CourseDetailSerializer(CourseSerializer):
    modules = ModuleSerializer(many=True, read_only=True)


class YogaPoseSerializer(serializers.ModelSerializer):
    class Meta:
        model = YogaPose
        fields = ['id', 'name', 'sanskrit_name', 'difficulty', 'description', 'instructions', 'image_url', 'video_url', 'created_at', 'updated_at']


class BreathingTechniqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreathingTechnique
        fields = ['id', 'name', 'sanskrit_name', 'description', 'instructions', 'duration', 'image_url', 'video_url', 'created_at', 'updated_at']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class BlogPostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPostCategory
        fields = ['id', 'name', 'slug', 'description']


class BlogCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = BlogComment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class BlogPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = BlogPostCategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'author', 'category', 'tags',
            'excerpt', 'content', 'featured_image', 'published_date',
            'is_published', 'comments_count', 'likes_count', 'is_liked',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False


class ConsultantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultant
        fields = ['id', 'name', 'specialty', 'bio', 'profile_picture_url', 'is_available']


class ConsultantDetailSerializer(serializers.ModelSerializer):
    """Full detail — only returned to authenticated users."""
    class Meta:
        model = Consultant
        fields = ['id', 'name', 'specialty', 'bio', 'profile_picture_url', 'is_available', 'contact_email', 'phone_number']


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'author_name', 'feedback_text', 'rating', 'submitted_at']
        read_only_fields = ['submitted_at']


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'sender', 'notification_type', 'message', 'link', 'read', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class LessonCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = LessonComment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DiscussionPostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionPost
        fields = ['id', 'topic', 'user', 'content', 'parent_post', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.likes.count()


class DiscussionTopicSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    posts_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionTopic
        fields = ['id', 'course', 'user', 'title', 'content', 'lesson', 'posts_count', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_posts_count(self, obj):
        return obj.posts.count()

    def get_likes_count(self, obj):
        return obj.likes.count()


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'course', 'course_title', 'amount', 'reference', 'status', 'paid_at', 'created_at']
        read_only_fields = ['reference', 'created_at']

    def get_course_title(self, obj):
        return obj.course.title if obj.course else None


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'full_name', 'email', 'phone_number', 'preferred_date', 'preferred_time', 'message', 'booked_at']
        read_only_fields = ['booked_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'submitted_at', 'is_read']
        read_only_fields = ['submitted_at', 'is_read']


class UserProgressSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    total_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()
    progress_percentage = serializers.IntegerField()
    is_completed = serializers.BooleanField()