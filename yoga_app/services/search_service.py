from django.db.models import Q, Avg, Count
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from yoga_app.models import YogaPose, BreathingTechnique, Course, BlogPost

try:
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    _POSTGRES_SEARCH_AVAILABLE = True
except ImportError:
    _POSTGRES_SEARCH_AVAILABLE = False


def is_postgres():
    return connection.vendor == 'postgresql' and _POSTGRES_SEARCH_AVAILABLE


class SearchService:
    @staticmethod
    def global_search(query='', category_filter='', pose_difficulty_filter='', course_price_filter=''):
        yoga_poses = YogaPose.objects.none()
        breathing_techniques = BreathingTechnique.objects.none()
        courses = Course.objects.none()

        if query:
            if is_postgres():
                search_query = SearchQuery(query, search_type='websearch')
                
                if not category_filter or category_filter == 'poses':
                    yoga_poses = YogaPose.objects.filter(
                        search_vector=search_query
                    ).annotate(
                        rank=SearchRank('search_vector', search_query)
                    ).order_by('-rank')

                if not category_filter or category_filter == 'breathing':
                    breathing_techniques = BreathingTechnique.objects.filter(
                        search_vector=search_query
                    ).annotate(
                        rank=SearchRank('search_vector', search_query)
                    ).order_by('-rank')

                if not category_filter or category_filter == 'courses':
                    courses = Course.objects.filter(
                        search_vector=search_query
                    ).annotate(
                        rank=SearchRank('search_vector', search_query)
                    ).order_by('-rank', '-is_popular')
            else:
                # Fallback for SQLite
                if not category_filter or category_filter == 'poses':
                    yoga_poses = YogaPose.objects.filter(
                        Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
                    ).distinct()

                if not category_filter or category_filter == 'breathing':
                    breathing_techniques = BreathingTechnique.objects.filter(
                        Q(name__icontains=query) | Q(sanskrit_name__icontains=query) | Q(description__icontains=query)
                    ).distinct()

                if not category_filter or category_filter == 'courses':
                    courses = Course.objects.filter(
                        Q(title__icontains=query) | Q(instructor_name__icontains=query) | Q(description__icontains=query)
                    ).distinct()
        else:
            if not category_filter or category_filter == 'poses':
                yoga_poses = YogaPose.objects.all()
            if not category_filter or category_filter == 'breathing':
                breathing_techniques = BreathingTechnique.objects.all()
            if not category_filter or category_filter == 'courses':
                courses = Course.objects.all()

        if pose_difficulty_filter and (not category_filter or category_filter == 'poses'):
            yoga_poses = yoga_poses.filter(difficulty=pose_difficulty_filter)

        if course_price_filter and (not category_filter or category_filter == 'courses'):
            if course_price_filter == 'free':
                courses = courses.filter(price=0.00)
            elif course_price_filter == 'paid':
                courses = courses.exclude(price=0.00)

        return {
            'yoga_poses': yoga_poses.order_by('name') if not query else yoga_poses,
            'breathing_techniques': breathing_techniques.order_by('name') if not query else breathing_techniques,
            'courses': courses.order_by('-is_popular', 'title') if not query else courses,
        }

    @staticmethod
    def get_suggestions(query, limit=5):
        if not query:
            return []

        suggestions = []

        if is_postgres():
            search_query = SearchQuery(query + ':*', search_type='raw')

            poses = YogaPose.objects.filter(
                search_vector=search_query
            ).annotate(
                rank=SearchRank('search_vector', search_query)
            ).values('id', 'name')[:limit]

            for pose in poses:
                suggestions.append({
                    'type': 'pose',
                    'title': pose['name'],
                    'url': f"/poses/{pose['id']}/"
                })

            techniques = BreathingTechnique.objects.filter(
                search_vector=search_query
            ).annotate(
                rank=SearchRank('search_vector', search_query)
            ).values('id', 'name')[:limit]

            for tech in techniques:
                suggestions.append({
                    'type': 'breathing',
                    'title': tech['name'],
                    'url': f"/breathing/{tech['id']}/"
                })

            courses = Course.objects.filter(
                search_vector=search_query
            ).annotate(
                rank=SearchRank('search_vector', search_query)
            ).values('id', 'title')[:limit]

            for course in courses:
                suggestions.append({
                    'type': 'course',
                    'title': course['title'],
                    'url': f"/courses/{course['id']}/"
                })

            blog_posts = BlogPost.objects.annotate(
                rank=SearchRank(
                    SearchVector('title', weight='A') + SearchVector('excerpt', weight='B'),
                    search_query
                )
            ).filter(rank__gt=0.1, is_published=True).values('slug', 'title')[:limit]

            for blog_post in blog_posts:
                suggestions.append({
                    'type': 'blog_post',
                    'title': blog_post['title'],
                    'url': f"/blog/{blog_post['slug']}/"
                })
        else:
            # Fallback for SQLite
            poses = YogaPose.objects.filter(
                Q(name__icontains=query) | Q(sanskrit_name__icontains=query)
            ).values('id', 'name')[:limit]

            for pose in poses:
                suggestions.append({
                    'type': 'pose',
                    'title': pose['name'],
                    'url': f"/poses/{pose['id']}/"
                })

            techniques = BreathingTechnique.objects.filter(
                Q(name__icontains=query) | Q(sanskrit_name__icontains=query)
            ).values('id', 'name')[:limit]

            for tech in techniques:
                suggestions.append({
                    'type': 'breathing',
                    'title': tech['name'],
                    'url': f"/breathing/{tech['id']}/"
                })

            courses = Course.objects.filter(
                Q(title__icontains=query) | Q(instructor_name__icontains=query)
            ).values('id', 'title')[:limit]

            for course in courses:
                suggestions.append({
                    'type': 'course',
                    'title': course['title'],
                    'url': f"/courses/{course['id']}/"
                })

            blog_posts = BlogPost.objects.filter(
                Q(title__icontains=query) | Q(excerpt__icontains=query),
                is_published=True
            ).values('slug', 'title')[:limit]

            for blog_post in blog_posts:
                suggestions.append({
                    'type': 'blog_post',
                    'title': blog_post['title'],
                    'url': f"/blog/{blog_post['slug']}/"
                })

        return suggestions

    @staticmethod
    def filter_courses(courses_list, query='', price_filter='', instructor_filter='', duration_filter='', min_rating_filter='', sort_by='popular_desc'):
        if query and is_postgres():
            search_query = SearchQuery(query, search_type='websearch')
            courses_list = courses_list.filter(
                search_vector=search_query
            ).annotate(
                rank=SearchRank('search_vector', search_query)
            ).order_by('-rank')
        elif query:
            courses_list = courses_list.filter(
                Q(title__icontains=query) |
                Q(instructor_name__icontains=query) |
                Q(description__icontains=query)
            ).distinct()

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
                courses_list = courses_list.annotate(avg_rating=Avg('reviews__rating')).filter(
                    Q(avg_rating__gte=min_rating) | Q(avg_rating__isnull=True)
                )
            except ValueError:
                pass

        if sort_by == 'newest':
            courses_list = courses_list.order_by('-created_at')
        elif sort_by == 'price_asc':
            courses_list = courses_list.order_by('price')
        elif sort_by == 'price_desc':
            courses_list = courses_list.order_by('-price')
        elif sort_by == 'alpha_asc':
            courses_list = courses_list.order_by('title')
        elif sort_by == 'rating_desc':
            if 'avg_rating' not in courses_list.query.annotations:
                courses_list = courses_list.annotate(avg_rating=Avg('reviews__rating'))
            courses_list = courses_list.order_by('-avg_rating')
        else:
            courses_list = courses_list.order_by('-is_popular', 'title')

        return courses_list

    @staticmethod
    def filter_blog_posts(query='', category_slug='', tag_slug='', author_id='', date_range='', sort_by='newest'):
        posts = BlogPost.objects.filter(is_published=True)

        if category_slug:
            from yoga_app.models import BlogPostCategory
            from django.shortcuts import get_object_or_404
            current_category = get_object_or_404(BlogPostCategory, slug=category_slug)
            posts = posts.filter(category=current_category)

        if tag_slug:
            from yoga_app.models import Tag
            from django.shortcuts import get_object_or_404
            current_tag = get_object_or_404(Tag, slug=tag_slug)
            posts = posts.filter(tags=current_tag)

        if author_id:
            from django.contrib.auth.models import User
            from django.shortcuts import get_object_or_404
            try:
                current_author = get_object_or_404(User, id=author_id)
                posts = posts.filter(author=current_author)
            except ValueError:
                pass

        if date_range:
            today = timezone.now().date()
            if date_range == 'past_week':
                posts = posts.filter(published_date__gte=today - timedelta(days=7))
            elif date_range == 'past_month':
                posts = posts.filter(published_date__gte=today - timedelta(days=30))
            elif date_range == 'past_year':
                posts = posts.filter(published_date__gte=today - timedelta(days=365))

        if query and is_postgres():
            search_query = SearchQuery(query, search_type='websearch')
            posts = posts.annotate(
                rank=SearchRank(
                    SearchVector('title', weight='A') +
                    SearchVector('content', weight='B') +
                    SearchVector('excerpt', weight='C') +
                    SearchVector('author__username', weight='D'),
                    search_query
                )
            ).filter(rank__gt=0.1).order_by('-rank')
        elif query:
            posts = posts.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(author__username__icontains=query)
            ).distinct()

        if sort_by == 'oldest':
            posts = posts.order_by('published_date')
        elif sort_by == 'title_asc':
            posts = posts.order_by('title')
        elif sort_by == 'title_desc':
            posts = posts.order_by('-title')
        elif sort_by == 'most_liked':
            posts = posts.annotate(likes_count=Count('likes')).order_by('-likes_count', '-published_date')
        else:
            posts = posts.order_by('-published_date')

        return posts
