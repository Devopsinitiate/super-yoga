from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from yoga_app.models import YogaPose
from yoga_app.services import SearchService


def global_search_view(request):
    query = request.GET.get('q', '')
    category_filter = request.GET.get('category', '')
    pose_difficulty_filter = request.GET.get('pose_difficulty', '')
    course_price_filter = request.GET.get('course_price', '')

    results = SearchService.global_search(
        query=query,
        category_filter=category_filter,
        pose_difficulty_filter=pose_difficulty_filter,
        course_price_filter=course_price_filter,
    )

    context = {
        'query': query,
        'category_filter': category_filter,
        'pose_difficulty_filter': pose_difficulty_filter,
        'course_price_filter': course_price_filter,
        'yoga_poses': results['yoga_poses'],
        'breathing_techniques': results['breathing_techniques'],
        'courses': results['courses'],
        'difficulty_choices': YogaPose.DIFFICULTY_CHOICES,
    }
    return render(request, 'yoga_app/search_results.html', context)


@ratelimit(key='ip', rate='30/m', block=True)
def global_search_suggestions_api(request):
    query = request.GET.get('q', '')
    suggestions = SearchService.get_suggestions(query)
    return JsonResponse({'suggestions': suggestions})


def about_view(request):
    return render(request, 'yoga_app/about.html')


def privacy_policy_view(request):
    return render(request, 'yoga_app/privacy_policy.html')


def terms_of_service_view(request):
    return render(request, 'yoga_app/terms_of_service.html')
