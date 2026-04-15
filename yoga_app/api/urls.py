from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from . import viewsets

router = DefaultRouter()
router.register(r'courses', viewsets.CourseViewSet, basename='api-course')
router.register(r'poses', viewsets.YogaPoseViewSet, basename='api-pose')
router.register(r'breathing', viewsets.BreathingTechniqueViewSet, basename='api-breathing')
router.register(r'blog', viewsets.BlogPostViewSet, basename='api-blog')
router.register(r'consultants', viewsets.ConsultantViewSet, basename='api-consultant')
router.register(r'notifications', viewsets.NotificationViewSet, basename='api-notification')
router.register(r'users', viewsets.UserViewSet, basename='api-user')
router.register(r'profile', viewsets.UserProfileViewSet, basename='api-profile')
router.register(r'testimonials', viewsets.TestimonialViewSet, basename='api-testimonial')
router.register(r'bookings', viewsets.BookingViewSet, basename='api-booking')
router.register(r'contact', viewsets.ContactMessageViewSet, basename='api-contact')
router.register(r'search', viewsets.SearchViewSet, basename='api-search')

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # OpenAPI schema & docs
    path('v1/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('v1/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
    path('v1/redoc/', SpectacularRedocView.as_view(url_name='api-schema'), name='api-redoc'),
]
