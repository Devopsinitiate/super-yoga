from .models import UserProfile


def user_profile_processor(request):
    """
    Adds user_profile to every template context.
    Uses request.user_profile set by UserProfileMiddleware when available,
    falling back to a DB query only if the middleware hasn't run.
    """
    if not request.user.is_authenticated:
        return {}

    # UserProfileMiddleware attaches this — avoids a second DB hit
    profile = getattr(request, 'user_profile', None)
    if profile is None:
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = None

    return {'user_profile': profile}
