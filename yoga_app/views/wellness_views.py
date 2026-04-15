"""
Views for Mudra Library, Meditation Library, Chakra Guide, and Daily Practice Journal.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone

from yoga_app.models import Mudra, Meditation, Chakra, DailyPractice, YogaPose, BreathingTechnique, KriyaSession

logger = logging.getLogger(__name__)


# ─── Mudra Library ────────────────────────────────────────────────────────────

def mudra_list_view(request):
    mudras = Mudra.objects.all()

    query = request.GET.get('q', '')
    difficulty = request.GET.get('difficulty', '')
    chakra = request.GET.get('chakra', '')

    if query:
        mudras = mudras.filter(
            Q(name__icontains=query) |
            Q(sanskrit_name__icontains=query) |
            Q(description__icontains=query) |
            Q(benefits__icontains=query)
        )
    if difficulty:
        mudras = mudras.filter(difficulty=difficulty)
    if chakra:
        mudras = mudras.filter(associated_chakra=chakra)

    featured = mudras.filter(is_featured=True).first()

    context = {
        'mudras': mudras,
        'featured': featured,
        'query': query,
        'difficulty_filter': difficulty,
        'chakra_filter': chakra,
        'difficulty_choices': Mudra.DIFFICULTY_CHOICES,
        'chakra_choices': Mudra.CHAKRA_CHOICES,
        'total_count': mudras.count(),
    }
    return render(request, 'yoga_app/mudra_list.html', context)


def mudra_detail_view(request, mudra_id):
    mudra = get_object_or_404(Mudra, id=mudra_id)
    related = Mudra.objects.filter(
        Q(associated_chakra=mudra.associated_chakra) | Q(difficulty=mudra.difficulty)
    ).exclude(id=mudra.id)[:4]

    context = {
        'mudra': mudra,
        'related_mudras': related,
    }
    return render(request, 'yoga_app/mudra_detail.html', context)


# ─── Meditation Library ───────────────────────────────────────────────────────

def meditation_list_view(request):
    meditations = Meditation.objects.all()

    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')

    if query:
        meditations = meditations.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(guided_by__icontains=query)
        )
    if category:
        meditations = meditations.filter(category=category)
    if difficulty:
        meditations = meditations.filter(difficulty=difficulty)

    featured = meditations.filter(is_featured=True).first()

    context = {
        'meditations': meditations,
        'featured': featured,
        'query': query,
        'category_filter': category,
        'difficulty_filter': difficulty,
        'category_choices': Meditation.CATEGORY_CHOICES,
        'difficulty_choices': Meditation.DIFFICULTY_CHOICES,
        'total_count': meditations.count(),
    }
    return render(request, 'yoga_app/meditation_list.html', context)


def meditation_detail_view(request, meditation_id):
    meditation = get_object_or_404(Meditation, id=meditation_id)
    related = Meditation.objects.filter(category=meditation.category).exclude(id=meditation.id)[:4]

    context = {
        'meditation': meditation,
        'related_meditations': related,
    }
    return render(request, 'yoga_app/meditation_detail.html', context)


# ─── Chakra Guide ─────────────────────────────────────────────────────────────

def chakra_guide_view(request):
    chakras = Chakra.objects.prefetch_related(
        'associated_poses', 'associated_mudras', 'associated_breathing'
    ).all()

    selected_key = request.GET.get('chakra', '')
    selected_chakra = None
    if selected_key:
        selected_chakra = chakras.filter(key=selected_key).first()

    context = {
        'chakras': chakras,
        'selected_chakra': selected_chakra or (chakras.first() if chakras.exists() else None),
    }
    return render(request, 'yoga_app/chakra_guide.html', context)


# ─── Daily Practice Journal ───────────────────────────────────────────────────

@login_required
def daily_practice_view(request):
    user = request.user
    today = timezone.localdate()

    # Get or initialise today's entry
    today_entry = DailyPractice.objects.filter(user=user, date=today).first()

    # Recent history (last 30 days)
    recent = DailyPractice.objects.filter(user=user).order_by('-date')[:30]

    # Streak calculation
    streak = 0
    check_date = today
    while DailyPractice.objects.filter(user=user, date=check_date).exists():
        streak += 1
        check_date = check_date - timezone.timedelta(days=1)

    # Stats
    total_sessions = DailyPractice.objects.filter(user=user).count()
    total_minutes = sum(p.duration_minutes for p in DailyPractice.objects.filter(user=user))

    context = {
        'today': today,
        'today_entry': today_entry,
        'recent_practices': recent,
        'streak': streak,
        'total_sessions': total_sessions,
        'total_minutes': total_minutes,
        'poses': YogaPose.objects.all().order_by('name'),
        'breathing_techniques': BreathingTechnique.objects.all().order_by('name'),
        'mudras': Mudra.objects.all().order_by('name'),
        'meditations': Meditation.objects.all().order_by('title'),
        'kriyas': KriyaSession.objects.all().order_by('name'),
        'mood_choices': DailyPractice.MOOD_CHOICES,
    }
    return render(request, 'yoga_app/daily_practice.html', context)


@login_required
def log_practice_view(request):
    """Create or update today's practice entry."""
    if request.method != 'POST':
        return redirect('daily_practice')

    user = request.user
    today = timezone.localdate()

    entry, _ = DailyPractice.objects.get_or_create(user=user, date=today)

    entry.mood_before = request.POST.get('mood_before', '')
    entry.mood_after = request.POST.get('mood_after', '')
    entry.duration_minutes = int(request.POST.get('duration_minutes', 0) or 0)
    entry.notes = request.POST.get('notes', '')
    entry.save()

    # Update M2M fields
    pose_ids = request.POST.getlist('poses')
    breathing_ids = request.POST.getlist('breathing_techniques')
    mudra_ids = request.POST.getlist('mudras')
    meditation_ids = request.POST.getlist('meditations')

    entry.poses.set(YogaPose.objects.filter(id__in=pose_ids))
    entry.breathing_techniques.set(BreathingTechnique.objects.filter(id__in=breathing_ids))
    entry.mudras.set(Mudra.objects.filter(id__in=mudra_ids))
    entry.meditations.set(Meditation.objects.filter(id__in=meditation_ids))

    kriya_ids = request.POST.getlist('kriyas')
    entry.kriyas.set(KriyaSession.objects.filter(id__in=kriya_ids))

    messages.success(request, "Your practice has been logged. Well done!")
    return redirect('daily_practice')


# ─── Kriya Sessions ───────────────────────────────────────────────────────────

from yoga_app.models import KriyaSession, KriyaStep  # noqa: E402 (appended import)


def kriya_list_view(request):
    kriyas = KriyaSession.objects.all()

    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')

    if query:
        kriyas = kriyas.filter(
            Q(name__icontains=query) |
            Q(sanskrit_name__icontains=query) |
            Q(description__icontains=query)
        )
    if category:
        kriyas = kriyas.filter(category=category)
    if difficulty:
        kriyas = kriyas.filter(difficulty=difficulty)

    featured = kriyas.filter(is_featured=True).first()

    context = {
        'kriyas': kriyas,
        'featured': featured,
        'query': query,
        'category_filter': category,
        'difficulty_filter': difficulty,
        'category_choices': KriyaSession.CATEGORY_CHOICES,
        'difficulty_choices': KriyaSession.DIFFICULTY_CHOICES,
        'total_count': kriyas.count(),
    }
    return render(request, 'yoga_app/kriya_list.html', context)


def kriya_detail_view(request, kriya_id):
    kriya = get_object_or_404(
        KriyaSession.objects.prefetch_related(
            'steps__pose', 'steps__breathing', 'steps__mudra', 'steps__meditation'
        ),
        id=kriya_id
    )
    related = KriyaSession.objects.filter(
        Q(category=kriya.category) | Q(difficulty=kriya.difficulty)
    ).exclude(id=kriya.id)[:4]

    context = {
        'kriya': kriya,
        'steps': kriya.steps.all(),
        'related_kriyas': related,
    }
    return render(request, 'yoga_app/kriya_detail.html', context)
