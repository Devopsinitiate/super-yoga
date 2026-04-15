from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from yoga_app.models import CourseReview, Course


class ReviewService:
    @staticmethod
    def get_course_reviews(course):
        return CourseReview.objects.filter(course=course).select_related('user').order_by('-submitted_at')

    @staticmethod
    def get_review_stats(course):
        reviews = CourseReview.objects.filter(course=course)
        return {
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'],
            'total_reviews': reviews.count(),
        }

    @staticmethod
    def get_user_review(course, user):
        return CourseReview.objects.filter(course=course, user=user).first()

    @staticmethod
    def submit_or_update_review(course, user, rating, comment=''):
        existing_review = CourseReview.objects.filter(course=course, user=user).first()

        if existing_review:
            existing_review.rating = rating
            if comment:
                existing_review.comment = comment
            existing_review.save()
            return existing_review, 'updated'
        else:
            review = CourseReview.objects.create(
                course=course,
                user=user,
                rating=rating,
                comment=comment if comment else '',
            )
            return review, 'created'
