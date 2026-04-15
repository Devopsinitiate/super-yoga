import logging
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.db import connection
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_page
from yoga_app.models import YogaPose, BreathingTechnique

logger = logging.getLogger(__name__)


def is_postgres():
    return connection.vendor == 'postgresql'


@cache_page(60 * 5)  # 5 minutes — golden ratio: 5 ≈ φ²
def pose_list_view(request):
    poses_list = YogaPose.objects.all().order_by('name')

    query = request.GET.get('q')
    if query:
        if is_postgres():
            from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
            search_query = SearchQuery(query, search_type='websearch')
            poses_list = YogaPose.objects.annotate(
                rank=SearchRank(
                    SearchVector('name', weight='A') +
                    SearchVector('sanskrit_name', weight='B') +
                    SearchVector('description', weight='C'),
                    search_query
                )
            ).filter(rank__gt=0.1).order_by('-rank')
        else:
            poses_list = YogaPose.objects.filter(
                Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
            ).distinct()

    difficulty_filter = request.GET.get('difficulty')
    if difficulty_filter:
        poses_list = poses_list.filter(difficulty=difficulty_filter)

    paginator = Paginator(poses_list, 9)
    page = request.GET.get('page')
    try:
        yoga_poses = paginator.page(page)
    except PageNotAnInteger:
        yoga_poses = paginator.page(1)
    except EmptyPage:
        yoga_poses = paginator.page(paginator.num_pages)

    context = {
        'yoga_poses': yoga_poses,
        'query': query,
        'difficulty_filter': difficulty_filter,
        'difficulty_choices': YogaPose.DIFFICULTY_CHOICES,
    }
    return render(request, 'yoga_app/pose_list.html', context)


def pose_detail_view(request, pose_id):
    pose = get_object_or_404(YogaPose, id=pose_id)
    related_poses = YogaPose.objects.exclude(id=pose_id).order_by('?')[:3]
    context = {
        'pose': pose,
        'related_poses': related_poses,
        'pose_list': YogaPose.objects.exclude(id=pose_id)[:3],
    }
    return render(request, 'yoga_app/pose_detail.html', context)


@cache_page(60 * 8)  # 8 minutes ≈ 5 × φ
def breathing_list_view(request):
    techniques_list = BreathingTechnique.objects.all().order_by('name')

    query = request.GET.get('q')
    if query:
        if is_postgres():
            from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
            search_query = SearchQuery(query, search_type='websearch')
            techniques_list = BreathingTechnique.objects.annotate(
                rank=SearchRank(
                    SearchVector('name', weight='A') +
                    SearchVector('sanskrit_name', weight='B') +
                    SearchVector('description', weight='C'),
                    search_query
                )
            ).filter(rank__gt=0.1).order_by('-rank')
        else:
            techniques_list = BreathingTechnique.objects.filter(
                Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
            ).distinct()

    paginator = Paginator(techniques_list, 6)
    page = request.GET.get('page')
    try:
        breathing_techniques = paginator.page(page)
    except PageNotAnInteger:
        breathing_techniques = paginator.page(1)
    except EmptyPage:
        breathing_techniques = paginator.page(paginator.num_pages)

    context = {
        'breathing_techniques': breathing_techniques,
        'query': query,
    }
    return render(request, 'yoga_app/breathing_list.html', context)


def breathing_technique_detail_view(request, technique_id):
    technique = get_object_or_404(BreathingTechnique, id=technique_id)
    context = {'technique': technique}
    return render(request, 'yoga_app/breathing_technique_detail.html', context)
