from __future__ import annotations
import logging
from typing import Any
from django.contrib.auth.models import User
from django.db.models import Count, Q, Case, When, IntegerField
from yoga_app.models import Course, Lesson, UserProfile, UserLessonCompletion, UserCourseCompletion

logger = logging.getLogger(__name__)


class ProgressService:

    @staticmethod
    def get_course_progress(user: User, course: Course) -> dict[str, Any]:
        total_lessons = Lesson.objects.filter(module__course=course).count()
        if total_lessons == 0:
            return {'total': 0, 'completed': 0, 'percentage': 0, 'is_complete': False}
        completed_count = UserLessonCompletion.objects.filter(
            user=user, lesson__module__course=course,
        ).count()
        percentage = int((completed_count / total_lessons) * 100)
        is_complete = UserCourseCompletion.objects.filter(user=user, course=course).exists()
        return {'total': total_lessons, 'completed': completed_count, 'percentage': percentage, 'is_complete': is_complete}

    @staticmethod
    def get_completed_lesson_ids(user: User, course: Course) -> set[int]:
        return set(UserLessonCompletion.objects.filter(
            user=user, lesson__module__course=course,
        ).values_list('lesson__id', flat=True))

    @staticmethod
    def get_user_dashboard_data(user: User) -> dict[str, Any]:
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # Get IDs of courses the user has completed
        completed_course_ids = set(
            UserCourseCompletion.objects.filter(user=user).values_list('course_id', flat=True)
        )

        enrolled_courses = profile.enrolled_courses.annotate(
            total_lessons_count=Count('modules__lessons', distinct=True),
            completed_lessons_count=Count(
                'modules__lessons__userlessoncompletion',
                filter=Q(modules__lessons__userlessoncompletion__user=user),
                distinct=True,
            ),
        )
        courses_data: list[dict[str, Any]] = []
        for course in enrolled_courses:
            total = course.total_lessons_count or 0
            completed = course.completed_lessons_count or 0
            percentage = int((completed / total) * 100) if total > 0 else 0
            is_completed = course.id in completed_course_ids
            courses_data.append({
                'course': course,
                'is_completed': is_completed,
                'total_lessons': total,
                'completed_lessons_count': completed,
                'progress_percentage': percentage,
            })
        completed_courses_count = len(completed_course_ids)
        last_viewed_lesson = None
        if profile.last_viewed_lesson_id:
            try:
                last_viewed_lesson = Lesson.objects.select_related('module__course').get(
                    id=profile.last_viewed_lesson_id
                )
            except Lesson.DoesNotExist:
                logger.warning("last_viewed_lesson_id %s not found for user %s",
                               profile.last_viewed_lesson_id, user.username)
        return {
            'enrolled_courses_data': courses_data,
            'user_profile': profile,
            'completed_courses_count': completed_courses_count,
            'last_viewed_lesson': last_viewed_lesson,
        }
