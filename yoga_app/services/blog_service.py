from django.db.models import Count, Q, Prefetch
from django.shortcuts import get_object_or_404
from yoga_app.models import BlogPost, BlogPostCategory, Tag


class BlogService:
    @staticmethod
    def get_blog_detail(post_slug):
        post = get_object_or_404(
            BlogPost.objects.select_related('author').prefetch_related(
                'comments__user', 'tags', 'likes', 'category'
            ),
            slug=post_slug,
            is_published=True
        )
        comments = post.comments.all().order_by('created_at')
        return post, comments

    @staticmethod
    def is_liked_by_user(post, user):
        if not user or not user.is_authenticated:
            return False
        return post.likes.filter(id=user.id).exists()

    @staticmethod
    def get_related_posts(post, limit=4):
        related_posts = BlogPost.objects.filter(is_published=True).exclude(id=post.id)

        if post.tags.exists():
            current_post_tag_ids = list(post.tags.values_list('id', flat=True))
            related_posts = related_posts.filter(tags__in=current_post_tag_ids).distinct()
            related_posts = related_posts.annotate(
                shared_tags_count=Count('tags', filter=Q(tags__in=current_post_tag_ids))
            ).order_by('-shared_tags_count', '-published_date')

        if related_posts.count() < limit and post.category:
            category_related = BlogPost.objects.filter(
                is_published=True,
                category=post.category
            ).exclude(id=post.id).order_by('-published_date')

            combined = list(related_posts)
            seen_ids = {p.id for p in combined}

            for p in category_related:
                if p.id not in seen_ids:
                    combined.append(p)
                    seen_ids.add(p.id)
            related_posts = combined

        return related_posts[:limit]

    @staticmethod
    def get_recent_posts(exclude_slug=None, limit=5):
        qs = BlogPost.objects.filter(is_published=True).order_by('-published_date')
        if exclude_slug:
            qs = qs.exclude(slug=exclude_slug)
        return qs[:limit]

    @staticmethod
    def get_categories():
        return BlogPostCategory.objects.all().order_by('name')

    @staticmethod
    def get_tags():
        return Tag.objects.all().order_by('name')

    @staticmethod
    def get_authors():
        from django.contrib.auth.models import User
        return User.objects.filter(blog_posts__isnull=False).distinct().order_by('username')
