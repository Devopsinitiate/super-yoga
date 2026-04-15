import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.db import connection
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from yoga_app.models import Course, Module, Lesson, UserProfile, UserCourseCompletion, UserLessonCompletion, LessonComment
from yoga_app.forms import CourseReviewForm, LessonCommentForm
from yoga_app.services import EnrollmentService, ProgressService, ReviewService, SearchService

logger = logging.getLogger(__name__)


def is_postgres():
    return connection.vendor == 'postgresql'


@vary_on_cookie
@cache_page(60 * 5)  # 5 minutes, varies per session so enrolled state is correct
def course_list_view(request):
    courses_list = Course.objects.all().prefetch_related('reviews')

    query = request.GET.get('q')
    price_filter = request.GET.get('price_filter')
    instructor_filter = request.GET.get('instructor_filter')
    duration_filter = request.GET.get('duration_filter')
    min_rating_filter = request.GET.get('min_rating_filter')
    sort_by = request.GET.get('sort_by', 'popular_desc')

    if query:
        if is_postgres():
            from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
            search_query = SearchQuery(query, search_type='websearch')
            courses_list = courses_list.annotate(
                rank=SearchRank(
                    SearchVector('title', weight='A') +
                    SearchVector('instructor_name', weight='B') +
                    SearchVector('description', weight='C'),
                    search_query
                )
            ).filter(rank__gt=0.1).order_by('-rank')
        else:
            courses_list = courses_list.filter(
                Q(title__icontains=query) | 
                Q(instructor_name__icontains=query) | 
                Q(description__icontains=query)
            ).distinct()
    else:
        if sort_by == 'rating_desc':
            courses_list = courses_list.annotate(avg_rating=Avg('reviews__rating'))

        if sort_by == 'newest':
            courses_list = courses_list.order_by('-created_at')
        elif sort_by == 'price_asc':
            courses_list = courses_list.order_by('price')
        elif sort_by == 'price_desc':
            courses_list = courses_list.order_by('-price')
        elif sort_by == 'alpha_asc':
            courses_list = courses_list.order_by('title')
        elif sort_by == 'rating_desc':
            courses_list = courses_list.order_by('-avg_rating')
        else:
            courses_list = courses_list.order_by('-is_popular', 'title')

    if price_filter == 'free':
        courses_list = courses_list.filter(price=0.00)
    elif price_filter == 'paid':
        courses_list = courses_list.exclude(price=0.00)

    if instructor_filter:
        courses_list = courses_list.filter(instructor_name__icontains=instructor_filter)

    if duration_filter:
        courses_list = courses_list.filter(duration__icontains=duration_filter)

    if min_rating_filter:
        try:
            min_rating = float(min_rating_filter)
            if 'avg_rating' not in courses_list.query.annotations:
                courses_list = courses_list.annotate(avg_rating=Avg('reviews__rating'))
            courses_list = courses_list.filter(
                Q(avg_rating__gte=min_rating) | Q(avg_rating__isnull=True)
            )
        except ValueError:
            pass

    paginator = Paginator(courses_list, 9)
    page = request.GET.get('page')
    try:
        courses = paginator.page(page)
    except PageNotAnInteger:
        courses = paginator.page(1)
    except EmptyPage:
        courses = paginator.page(paginator.num_pages)

    all_instructors = Course.objects.values_list('instructor_name', flat=True).distinct().order_by('instructor_name')
    all_durations = Course.objects.values_list('duration', flat=True).distinct().order_by('duration')

    # Build set of enrolled course IDs for the current user so the template can show badges
    enrolled_course_ids = set()
    if request.user.is_authenticated:
        try:
            from yoga_app.models import UserProfile
            profile = UserProfile.objects.get(user=request.user)
            enrolled_course_ids = set(profile.enrolled_courses.values_list('id', flat=True))
        except Exception:
            pass

    context = {
        'courses': courses,
        'query': query,
        'price_filter': price_filter,
        'instructor_filter': instructor_filter,
        'duration_filter': duration_filter,
        'min_rating_filter': min_rating_filter,
        'sort_by': sort_by,
        'all_instructors': all_instructors,
        'all_durations': all_durations,
        'enrolled_course_ids': enrolled_course_ids,
    }
    return render(request, 'yoga_app/course_list.html', context)


def course_detail_view(request, course_id):
    course = get_object_or_404(Course.objects.prefetch_related('reviews'), id=course_id)
    
    is_enrolled = False
    is_completed = False
    review_form = None
    user_review = None
    
    if request.user.is_authenticated:
        user = request.user
        is_enrolled = EnrollmentService.is_enrolled(user, course)
        
        if is_enrolled:
            is_completed = UserCourseCompletion.objects.filter(user=user, course=course).exists()
            user_review = ReviewService.get_user_review(course, user)
            review_form = CourseReviewForm(instance=user_review) if user_review else CourseReviewForm()

    reviews = ReviewService.get_course_reviews(course)
    review_stats = ReviewService.get_review_stats(course)

    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'is_completed': is_completed,
        'review_form': review_form,
        'user_review': user_review,
        'reviews': reviews,
        'average_rating': review_stats['average_rating'],
        'total_reviews_count': review_stats['total_reviews'],
    }
    return render(request, 'yoga_app/course_detail.html', context)


@login_required
def course_content_view(request, course_id, lesson_id=None):
    user = request.user
    course = get_object_or_404(Course, id=course_id)
    user_profile = get_object_or_404(UserProfile, user=user)

    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You are not enrolled in '{course.title}'. Please enroll to access the full content.")
        return redirect('course_detail', course_id=course.id)

    all_lessons_in_course = Lesson.objects.filter(module__course=course).select_related('module').order_by('module__order', 'order')

    current_lesson = None
    if lesson_id:
        current_lesson = get_object_or_404(all_lessons_in_course, id=lesson_id)
    else:
        if user_profile.last_viewed_lesson and user_profile.last_viewed_lesson.module.course == course:
            current_lesson = user_profile.last_viewed_lesson
        elif all_lessons_in_course.exists():
            current_lesson = all_lessons_in_course.first()

    comment_form = None
    if current_lesson:
        if request.method == 'POST':
            comment_form = LessonCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.lesson = current_lesson
                comment.user = user
                comment.save()
                messages.success(request, "Your comment has been added successfully!")
                return redirect('course_content', course_id=course_id, lesson_id=current_lesson.id)
            else:
                messages.error(request, "There was an error adding your comment. Please correct the highlighted fields.")
        else:
            comment_form = LessonCommentForm()

    lesson_comments = []
    if current_lesson:
        lesson_comments = LessonComment.objects.filter(lesson=current_lesson).select_related('user').order_by('created_at')

    if current_lesson:
        EnrollmentService.update_last_viewed_lesson(user, current_lesson)

    previous_lesson = None
    next_lesson = None
    if current_lesson:
        # Use ORM ordering to avoid loading all lessons into memory
        previous_lesson = (
            all_lessons_in_course
            .filter(
                Q(module__order__lt=current_lesson.module.order) |
                Q(module__order=current_lesson.module.order, order__lt=current_lesson.order)
            )
            .last()
        )
        next_lesson = (
            all_lessons_in_course
            .filter(
                Q(module__order__gt=current_lesson.module.order) |
                Q(module__order=current_lesson.module.order, order__gt=current_lesson.order)
            )
            .first()
        )

    progress_data = ProgressService.get_course_progress(user, course)
    completed_lesson_ids = ProgressService.get_completed_lesson_ids(user, course)

    course_is_completed_by_user = UserCourseCompletion.objects.filter(user=user, course=course).exists()
    modules = Module.objects.filter(course=course).prefetch_related('lessons').order_by('order')

    context = {
        'course': course,
        'modules': modules,
        'current_lesson': current_lesson,
        'completed_lesson_ids': completed_lesson_ids,
        'total_lessons': progress_data['total'],
        'completed_lessons_count': progress_data['completed'],
        'progress_percentage': progress_data['percentage'],
        'course_is_completed_by_user': course_is_completed_by_user,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'comment_form': comment_form,
        'lesson_comments': lesson_comments,
    }
    return render(request, 'yoga_app/course_content.html', context)


@login_required
def submit_course_review_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, "You must be enrolled in this course to submit or edit a review.")
        return redirect('course_detail', course_id=course.id)

    existing_review = ReviewService.get_user_review(course, user)

    if request.method == 'POST':
        form = CourseReviewForm(request.POST, instance=existing_review) if existing_review else CourseReviewForm(request.POST)

        if form.is_valid():
            review, action = ReviewService.submit_or_update_review(
                course=course,
                user=user,
                rating=form.cleaned_data['rating'],
                comment=form.cleaned_data.get('comment', ''),
            )
            messages.success(request, 'Your review has been submitted/updated successfully!')
            return redirect('course_detail', course_id=course_id)
        else:
            messages.error(request, 'There was an error submitting/updating your review. Please correct the highlighted fields.')

            # Re-use course_detail_view's full context to avoid template errors
            reviews = ReviewService.get_course_reviews(course)
            review_stats = ReviewService.get_review_stats(course)
            is_completed = UserCourseCompletion.objects.filter(user=user, course=course).exists()

            context = {
                'course': course,
                'is_enrolled': True,
                'is_completed': is_completed,
                'review_form': form,
                'user_review': existing_review,
                'reviews': reviews,
                'average_rating': review_stats['average_rating'],
                'total_reviews_count': review_stats['total_reviews'],
                # modules needed by course_detail template sidebar
                'modules': course.modules.prefetch_related('lessons').order_by('order'),
            }
            return render(request, 'yoga_app/course_detail.html', context)
    else:
        messages.error(request, 'Invalid request method for submitting/editing a review.')
        return redirect('course_detail', course_id=course_id)


@login_required
def enroll_free_course_view(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)

        if not course.is_free:
            messages.error(request, "This course is not free. Please use the payment gateway to enroll.")
            return redirect('course_detail', course_id=course.id)

        success, status = EnrollmentService.enroll_free_course(request.user, course)

        if success:
            messages.success(request, f"You have successfully enrolled in '{course.title}'!")
            return redirect('dashboard')
        elif status == 'already_enrolled':
            messages.info(request, f"You are already enrolled in '{course.title}'.")
            return redirect('dashboard')
        else:
            messages.error(request, "An unexpected error occurred during enrollment.")
            return redirect('course_detail', course_id=course.id)
    else:
        messages.error(request, "Invalid request for free course enrollment.")
        return redirect('home')


@login_required 
def mark_course_complete_view(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course.id).exists():
            messages.error(request, f"You are not enrolled in '{course.title}'. Cannot mark as complete.")
            return redirect('course_detail', course_id=course.id)

        success, status = EnrollmentService.mark_course_complete(user, course)
        
        if success:
            messages.success(request, f"Congratulations! You have completed '{course.title}'!")
        elif status == 'already_complete':
            messages.info(request, f"This course is already marked as complete for you.")
        elif status == 'lessons_incomplete':
            total_lessons = Lesson.objects.filter(module__course=course).count()
            completed_lessons_count = UserLessonCompletion.objects.filter(user=user, lesson__module__course=course).count()
            messages.error(request, f"Please complete all lessons ({completed_lessons_count}/{total_lessons}) in '{course.title}' before marking the course as complete.")
            return redirect('course_content_base', course_id=course.id)
        else:
            messages.error(request, f"An unexpected error occurred while marking '{course.title}' as complete.")
        
        return redirect('course_detail', course_id=course_id)
    else:
        messages.error(request, "Invalid request to mark course complete.")
        return redirect('home')


@login_required
def mark_lesson_complete_view(request, course_id, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id, module__course__id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course_id).exists():
            messages.error(request, f"You are not enrolled in '{lesson.module.course.title}'. Cannot mark lesson as complete.")
            return redirect('course_detail', course_id=course.id)

        success, status = EnrollmentService.mark_lesson_complete(user, lesson)
        
        if success:
            messages.success(request, f"Lesson '{lesson.title}' marked as complete!")
        elif status == 'already_complete':
            messages.info(request, f"Lesson '{lesson.title}' is already marked as complete.")
        else:
            messages.error(request, f"An error occurred while marking '{lesson.title}' as complete.")
        
        return redirect('course_content', course_id=course_id, lesson_id=lesson_id)
    else:
        messages.error(request, "Invalid request to mark lesson complete.")
        return redirect('course_content_base', course_id=course_id)
