from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from yoga_app.models import (
    UserProfile, Course, Module, Lesson, YogaPose, BreathingTechnique,
    BlogPost, BlogPostCategory, Tag, Consultant, Testimonial,
    CourseReview, DiscussionTopic, DiscussionPost, Notification,
    LessonComment, BlogComment, Payment, Booking, ContactMessage,
    UserLessonCompletion, UserCourseCompletion
)
from .serializers import (
    UserSerializer, UserProfileSerializer, CourseSerializer, CourseDetailSerializer,
    LessonSerializer, ModuleSerializer, YogaPoseSerializer, BreathingTechniqueSerializer,
    BlogPostSerializer, BlogPostCategorySerializer, TagSerializer,
    ConsultantSerializer, ConsultantDetailSerializer,
    TestimonialSerializer, CourseReviewSerializer, DiscussionTopicSerializer,
    DiscussionPostSerializer, NotificationSerializer, LessonCommentSerializer,
    BlogCommentSerializer, PaymentSerializer, BookingSerializer, ContactMessageSerializer,
    UserProgressSerializer
)
from yoga_app.services import (
    EnrollmentService, PaymentService, NotificationService,
    ProgressService, SearchService, BlogService, DiscussionService, ReviewService
)


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.prefetch_related('reviews', 'modules__lessons').order_by('-is_popular', 'price')
    serializer_class = CourseSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'instructor_name', 'description']
    ordering_fields = ['title', 'price', 'created_at', 'is_popular']
    ordering = ['-is_popular', 'price']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        price_filter = self.request.query_params.get('price_filter')
        instructor_filter = self.request.query_params.get('instructor_filter')
        duration_filter = self.request.query_params.get('duration_filter')

        if price_filter == 'free':
            queryset = queryset.filter(price=0.00)
        elif price_filter == 'paid':
            queryset = queryset.exclude(price=0.00)

        if instructor_filter:
            queryset = queryset.filter(instructor_name__icontains=instructor_filter)

        if duration_filter:
            queryset = queryset.filter(duration__icontains=duration_filter)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        success, status_msg = EnrollmentService.enroll_free_course(request.user, course)
        if success:
            return Response({'message': f'Enrolled in {course.title}'}, status=status.HTTP_200_OK)
        return Response({'message': status_msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def progress(self, request, pk=None):
        course = self.get_object()
        progress = ProgressService.get_course_progress(request.user, course)
        return Response(progress)


class YogaPoseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = YogaPose.objects.all().order_by('name')
    serializer_class = YogaPoseSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sanskrit_name', 'description']
    ordering_fields = ['name', 'difficulty', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        return queryset


class BreathingTechniqueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BreathingTechnique.objects.all().order_by('name')
    serializer_class = BreathingTechniqueSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'sanskrit_name', 'description']


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.filter(is_published=True).select_related('author', 'category').prefetch_related('tags', 'likes').order_by('-published_date')
    serializer_class = BlogPostSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'excerpt', 'author__username']
    ordering_fields = ['published_date', 'title']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get('category_slug')
        tag_slug = self.request.query_params.get('tag_slug')

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user
        if user in post.likes.all():
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True
        return Response({'liked': liked, 'likes_count': post.likes.count()})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def comment(self, request, pk=None):
        post = self.get_object()
        serializer = BlogCommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(post=post, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Consultant.objects.filter(is_available=True).order_by('name')
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return ConsultantDetailSerializer
        return ConsultantSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related('sender').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(recipient=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response({'message': 'All notifications marked as read'})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dashboard(self, request):
        dashboard_data = ProgressService.get_user_dashboard_data(request.user)
        profile = dashboard_data.pop('user_profile', None)
        last_lesson = dashboard_data.pop('last_viewed_lesson', None)
        dashboard_data['user_profile'] = UserProfileSerializer(profile).data if profile else None
        dashboard_data['last_viewed_lesson'] = {
            'id': last_lesson.id,
            'title': last_lesson.title,
            'course_id': last_lesson.module.course.id if last_lesson.module else None,
            'course_title': last_lesson.module.course.title if last_lesson.module else None,
        } if last_lesson else None
        return Response(dashboard_data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def progress(self, request):
        courses = request.user.profile.enrolled_courses.all()
        progress_data = []
        for course in courses:
            p = ProgressService.get_course_progress(request.user, course)
            progress_data.append({
                'course_id': course.id,
                'course_title': course.title,
                **p
            })
        return Response(progress_data)


class SearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='global')
    def search_global(self, request):
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        results = SearchService.global_search(query=query, category_filter=category)
        return Response({
            'poses': YogaPoseSerializer(results['yoga_poses'][:10], many=True).data,
            'techniques': BreathingTechniqueSerializer(results['breathing_techniques'][:10], many=True).data,
            'courses': CourseSerializer(results['courses'][:10], many=True, context={'request': request}).data,
        })

    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        query = request.query_params.get('q', '')
        suggestions = SearchService.get_suggestions(query)
        return Response({'suggestions': suggestions})


class TestimonialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Testimonial.objects.filter(is_approved=True).order_by('-submitted_at')
    serializer_class = TestimonialSerializer
    pagination_class = StandardPagination


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().order_by('-booked_at')
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by('-submitted_at')
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        # Anyone can submit a contact message; only admins can list/read them
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
