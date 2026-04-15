# yoga_app/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    UserProfile, YogaPose, BreathingTechnique, Course, Module, Lesson,
    UserLessonCompletion, DiscussionTopic, DiscussionPost, UserCourseCompletion,
    CourseReview, Consultant, Testimonial, Booking, NewsletterSubscription,
    ContactMessage, Payment, Notification, LessonComment, BlogPostCategory, BlogPost, BlogComment,
    Tag,
    Mudra, Meditation, Chakra, DailyPractice,
    KriyaSession, KriyaStep,
)

# --- Inline Classes for Course Management ---

class LessonInline(admin.TabularInline):
    """
    Inline for Lessons to be managed directly within a Module.
    """
    model = Lesson
    extra = 1 # Number of empty forms to display
    # ADDED 'resources_content'
    fields = ('title', 'order', 'video_url', 'content', 'resources_content')
    # Use autocomplete_fields for ForeignKey if you have many lessons/modules
    # raw_id_fields = ('module',) # Not needed if used as inline
    show_change_link = True # Allows clicking to full lesson edit page
    verbose_name_plural = 'Lessons in this Module'

class ModuleInline(admin.StackedInline):
    """
    Inline for Modules to be managed directly within a Course.
    Uses StackedInline for better display of rich text fields.
    """
    model = Module
    extra = 1 # Number of empty forms to display
    show_change_link = True # Allows clicking to full module edit page
    fieldsets = (
        (None, {
            'fields': ('title', 'order', 'description'),
        }),
    )
    inlines = [LessonInline] # Nest LessonInline within ModuleInline
    verbose_name_plural = 'Modules in this Course'

# --- Custom Admin Classes for Models ---

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # NEW: Added 'profile_picture' and 'bio' to list_display
    list_display = ('user', 'last_viewed_lesson', 'enrolled_courses_count', 'profile_picture_thumbnail', 'bio_snippet')
    search_fields = ('user__username', 'user__email', 'bio') # NEW: Added 'bio' to search fields
    raw_id_fields = ('user', 'last_viewed_lesson') # Use raw_id_fields for ForeignKey/OneToOne to User
    filter_horizontal = ('enrolled_courses',) # Nicer widget for ManyToMany
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_picture', 'bio', 'last_viewed_lesson'), # NEW: Added profile_picture and bio
        }),
        ('Enrollment Information', {
            'fields': ('enrolled_courses',),
        }),
    )

    def enrolled_courses_count(self, obj):
        return obj.enrolled_courses.count()
    enrolled_courses_count.short_description = 'Enrolled Courses'

    # NEW: Method to display a thumbnail of the profile picture in the admin list
    def profile_picture_thumbnail(self, obj):
        if obj.profile_picture:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_picture.url)
        return "No Image"
    profile_picture_thumbnail.short_description = 'Picture'

    # NEW: Method to display a snippet of the bio in the admin list
    def bio_snippet(self, obj):
        return obj.bio[:50] + '...' if obj.bio and len(obj.bio) > 50 else obj.bio
    bio_snippet.short_description = 'Bio'


# Re-register UserProfile with the User model
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'
    fk_name = 'user'
    fieldsets = (
        (None, {
            # NEW: Added profile_picture and bio to the inline form
            'fields': ('profile_picture', 'bio', 'enrolled_courses', 'last_viewed_lesson'),
        }),
    )
    filter_horizontal = ('enrolled_courses',)
    
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = BaseUserAdmin.list_display + ('is_staff', 'is_active', 'date_joined')
    # REMOVED the problematic line: (None, {'fields': ('email',)}),
    # BaseUserAdmin already includes 'email' in its fieldsets.
    fieldsets = BaseUserAdmin.fieldsets # Keep original fieldsets from BaseUserAdmin


# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(YogaPose)
class YogaPoseAdmin(admin.ModelAdmin):
    list_display = ('name', 'sanskrit_name', 'difficulty', 'created_at', 'updated_at')
    list_filter = ('difficulty', 'created_at')
    search_fields = ('name', 'sanskrit_name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'sanskrit_name', 'difficulty', 'image_url', 'video_url'),
        }),
        ('Content', {
            'fields': ('description', 'instructions'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',), # Collapsible section
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BreathingTechnique)
class BreathingTechniqueAdmin(admin.ModelAdmin):
    list_display = ('name', 'sanskrit_name', 'duration', 'created_at', 'updated_at')
    list_filter = ('duration', 'created_at')
    search_fields = ('name', 'sanskrit_name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'sanskrit_name', 'duration', 'image_url', 'video_url'),
        }),
        ('Content', {
            'fields': ('description', 'instructions'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor_name', 'price', 'is_free', 'is_popular', 'duration', 'created_at')
    list_filter = ('is_free', 'is_popular', 'instructor_name', 'duration')
    search_fields = ('title', 'instructor_name', 'description')
    inlines = [ModuleInline] # Add ModuleInline here
    fieldsets = (
        (None, {
            'fields': ('title', 'instructor_name', 'price', 'is_popular', 'duration', 'image_url', 'start_date'),
        }),
        ('Content', {
            'fields': ('description', 'overview_content', 'includes'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'is_free') # is_free is calculated automatically

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    raw_id_fields = ('course',) # Use raw_id_fields for ForeignKey
    inlines = [LessonInline] # Add LessonInline here
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'order', 'description'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'video_url', 'created_at')
    list_filter = ('module__course', 'module') # Filter by course then module
    search_fields = ('title', 'content', 'module__title', 'module__course__title')
    raw_id_fields = ('module',)
    fieldsets = (
        (None, {
            'fields': ('module', 'title', 'order', 'video_url'),
        }),
        ('Content', {
            'fields': ('content', 'resources_content'), # ADDED 'resources_content' here
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserLessonCompletion)
class UserLessonCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed_at')
    list_filter = ('user', 'lesson__module__course') # Filter by user and course
    search_fields = ('user__username', 'lesson__title', 'lesson__module__course__title')
    raw_id_fields = ('user', 'lesson')
    readonly_fields = ('completed_at',)

@admin.register(UserCourseCompletion)
class UserCourseCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'completed_at')
    list_filter = ('user', 'course')
    search_fields = ('user__username', 'course__title')
    raw_id_fields = ('user', 'course')
    readonly_fields = ('completed_at',)

@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('course', 'user', 'rating', 'submitted_at')
    list_filter = ('rating', 'course', 'user')
    search_fields = ('course__title', 'user__username', 'comment')
    raw_id_fields = ('course', 'user')
    readonly_fields = ('submitted_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('course', 'user', 'rating'),
        }),
        ('Review Details', {
            'fields': ('comment',),
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(DiscussionTopic)
class DiscussionTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'user', 'lesson', 'created_at', 'likes_count')
    list_filter = ('course', 'user', 'lesson')
    search_fields = ('title', 'content', 'course__title', 'user__username', 'lesson__title')
    raw_id_fields = ('course', 'user', 'lesson', 'likes') # Add 'likes' to raw_id_fields
    readonly_fields = ('created_at', 'updated_at', 'likes_count') # likes_count is a method
    filter_horizontal = ('likes',) # Nicer widget for ManyToMany

    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'

@admin.register(DiscussionPost)
class DiscussionPostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'created_at', 'content_snippet', 'likes_count') # Removed updated_at from list_display, added content_snippet
    list_filter = ('topic__course', 'user', 'created_at')
    search_fields = ('content', 'topic__title', 'user__username')
    raw_id_fields = ('topic', 'user', 'parent_post', 'likes') # Add 'likes' to raw_id_fields
    readonly_fields = ('created_at', 'updated_at', 'likes_count')
    filter_horizontal = ('likes',) # Nicer widget for ManyToMany

    def content_snippet(self, obj): # Added content_snippet method
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_snippet.short_description = 'Content'

    def likes_count(self, obj):
        return obj.likes.count()
    likes_count.short_description = 'Likes'

@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'is_available', 'contact_email', 'created_at')
    list_filter = ('is_available', 'specialty')
    search_fields = ('name', 'specialty', 'contact_email')
    fieldsets = (
        (None, {
            'fields': ('name', 'specialty', 'profile_picture_url', 'is_available'),
        }),
        ('Contact', {
            'fields': ('contact_email', 'phone_number'),
        }),
        ('Biography', {
            'fields': ('bio',),
            'classes': ('collapse',),
        }),
    )

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'rating', 'submitted_at', 'is_approved')
    list_filter = ('is_approved', 'rating')
    list_editable = ('is_approved',)  # approve/reject directly from the list
    search_fields = ('author_name', 'feedback_text')
    date_hierarchy = 'submitted_at'
    actions = ['mark_approved', 'mark_unapproved']

    def mark_approved(self, request, queryset):
        queryset.update(is_approved=True)
    mark_approved.short_description = "Mark selected testimonials as approved"

    def mark_unapproved(self, request, queryset):
        queryset.update(is_approved=False)
    mark_unapproved.short_description = "Mark selected testimonials as unapproved"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'user', 'preferred_date', 'preferred_time', 'booked_at')
    list_filter = ('preferred_date', 'preferred_time')
    search_fields = ('full_name', 'email', 'message', 'user__username')
    raw_id_fields = ('user',)
    readonly_fields = ('booked_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'full_name', 'email', 'phone_number'),
        }),
        ('Session Details', {
            'fields': ('preferred_date', 'preferred_time', 'message'),
        }),
        ('Timestamp', {
            'fields': ('booked_at',),
            'classes': ('collapse',),
        }),
    )

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at', 'is_read')
    list_filter = ('is_read', 'submitted_at')
    list_editable = ('is_read',)  # mark as read directly from the list
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('submitted_at',)
    actions = ['mark_as_read', 'mark_as_unread']
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'subject', 'is_read'),
        }),
        ('Message Content', {
            'fields': ('message',),
        }),
        ('Timestamp', {
            'fields': ('submitted_at',),
            'classes': ('collapse',),
        }),
    )

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Mark selected messages as unread"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'amount', 'status', 'reference', 'paid_at', 'verified_at')
    list_filter = ('status', 'paid_at', 'course')
    search_fields = ('user__username', 'course__title', 'reference') # Removed email as it's not on Payment model
    raw_id_fields = ('user', 'course')
    readonly_fields = ('paid_at', 'verified_at', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'course', 'amount', 'status', 'reference'),
        }),
        ('Timestamps', {
            'fields': ('paid_at', 'verified_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'message_snippet', 'read', 'created_at', 'link')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('recipient__username', 'sender__username', 'message', 'link')
    raw_id_fields = ('recipient', 'sender')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('recipient', 'sender', 'notification_type', 'message', 'link', 'read'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def message_snippet(self, obj):
        return obj.message[:75] + '...' if len(obj.message) > 75 else obj.message
    message_snippet.short_description = 'Message Snippet'

@admin.register(LessonComment) # NEW: Register LessonComment model
class LessonCommentAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'user', 'created_at', 'content_snippet')
    list_filter = ('lesson__module__course', 'lesson', 'user')
    search_fields = ('content', 'lesson__title', 'user__username')
    raw_id_fields = ('lesson', 'user')
    readonly_fields = ('created_at', 'updated_at')

    def content_snippet(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_snippet.short_description = 'Comment Snippet'


# NEW: Admin for BlogPostCategory
@admin.register(BlogPostCategory)
class BlogPostCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)} # Automatically populate slug from name
    search_fields = ('name',)

# NEW: Admin for BlogPost
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'published_date', 'is_published')
    list_filter = ('category', 'author', 'is_published', 'published_date')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category', 'is_published', 'published_date', 'featured_image')
        }),
        ('Content', {
            'fields': ('excerpt', 'content') # RichTextUploadingField for content
        }),
        ('Tags', { # NEW: Fieldset for tags
            'fields': ('tags',),
            'classes': ('collapse',),
        }),
    )
    # NEW: Add filter_horizontal for the ManyToMany 'tags' field
    filter_horizontal = ('tags',) 
    actions = ['mark_posts_published', 'mark_posts_unpublished']

    def mark_posts_published(self, request, queryset):
        queryset.update(is_published=True)
    mark_posts_published.short_description = "Mark selected posts as published"

    def mark_posts_unpublished(self, request, queryset):
        queryset.update(is_published=False)
    mark_posts_unpublished.short_description = "Mark selected posts as unpublished"

# NEW: Admin for BlogComment
@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at', 'content_snippet')
    list_filter = ('post', 'user', 'created_at')
    search_fields = ('post__title', 'user__username', 'content')
    date_hierarchy = 'created_at'
    raw_id_fields = ('post', 'user') # Use raw_id_fields for ForeignKey

    def content_snippet(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_snippet.short_description = 'Comment Snippet'

# NEW: Admin for Tag
@admin.register(Tag) # NEW: Register the Tag model
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)} # Automatically populate slug from name
    search_fields = ('name',)


# ─── Wellness Models ──────────────────────────────────────────────────────────

@admin.register(Mudra)
class MudraAdmin(admin.ModelAdmin):
    list_display = ('name', 'sanskrit_name', 'difficulty', 'associated_chakra', 'is_featured')
    list_filter = ('difficulty', 'associated_chakra', 'is_featured')
    search_fields = ('name', 'sanskrit_name', 'description', 'benefits')
    list_editable = ('is_featured',)
    ordering = ('name',)


@admin.register(Meditation)
class MeditationAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'duration_minutes', 'guided_by', 'is_featured')
    list_filter = ('category', 'difficulty', 'is_featured')
    search_fields = ('title', 'description', 'guided_by')
    list_editable = ('is_featured',)
    ordering = ('title',)


@admin.register(Chakra)
class ChakraAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'sanskrit_name', 'color', 'element', 'seed_mantra')
    filter_horizontal = ('associated_poses', 'associated_mudras', 'associated_breathing')
    ordering = ('number',)


@admin.register(DailyPractice)
class DailyPracticeAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'mood_before', 'mood_after', 'duration_minutes')
    list_filter = ('date', 'mood_after')
    search_fields = ('user__username', 'notes')
    filter_horizontal = ('poses', 'breathing_techniques', 'mudras', 'meditations')
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at')


# ─── Kriya Session ────────────────────────────────────────────────────────────

class KriyaStepInline(admin.TabularInline):
    model = KriyaStep
    extra = 1
    fields = ('order', 'step_type', 'pose', 'breathing', 'mudra', 'meditation',
              'duration_seconds', 'repetitions', 'instruction_note')
    ordering = ('order',)


@admin.register(KriyaSession)
class KriyaSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'difficulty', 'duration_minutes', 'step_count', 'is_featured')
    list_filter = ('category', 'difficulty', 'is_featured')
    search_fields = ('name', 'sanskrit_name', 'description')
    list_editable = ('is_featured',)
    inlines = [KriyaStepInline]
    ordering = ('name',)

    def step_count(self, obj):
        return obj.steps.count()
    step_count.short_description = 'Steps'
