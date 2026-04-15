from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from django.db import transaction
from yoga_app.models import BlogPost, BlogPostCategory, Tag
from yoga_app.forms import BlogCommentForm, BlogPostForm
from yoga_app.services import BlogService, SearchService, NotificationService


def blog_list_view(request): 
    query = request.GET.get('q')
    category_slug = request.GET.get('category_slug')
    tag_slug = request.GET.get('tag_slug')
    author_id = request.GET.get('author_id')
    date_range = request.GET.get('date_range')
    sort_by = request.GET.get('sort_by', 'newest')

    posts = SearchService.filter_blog_posts(
        query=query,
        category_slug=category_slug,
        tag_slug=tag_slug,
        author_id=author_id,
        date_range=date_range,
        sort_by=sort_by,
    )

    categories = BlogService.get_categories()
    tags = BlogService.get_tags()
    all_authors = BlogService.get_authors()
    recent_posts = BlogService.get_recent_posts(limit=5)

    current_category = None
    current_tag = None
    current_author = None
    date_range_filter = None

    if category_slug:
        current_category = get_object_or_404(BlogPostCategory, slug=category_slug)

    if tag_slug:
        current_tag = get_object_or_404(Tag, slug=tag_slug)

    if author_id:
        from django.contrib.auth.models import User
        try:
            current_author = get_object_or_404(User, id=author_id)
        except ValueError:
            pass

    if date_range:
        date_range_filter = date_range

    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    
    try:
        posts_page = paginator.page(page_number)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)

    context = {
        'posts': posts_page,
        'categories': categories,
        'tags': tags,
        'current_category': current_category,
        'current_tag': current_tag,
        'query': query,
        'recent_posts': recent_posts,
        'all_authors': all_authors,
        'current_author': current_author,
        'date_range_filter': date_range_filter,
        'sort_by': sort_by,
    }
    return render(request, 'yoga_app/blog_list.html', context)


def blog_detail_view(request, post_slug):
    post, comments = BlogService.get_blog_detail(post_slug)
    comment_form = BlogCommentForm()

    is_liked_by_user = BlogService.is_liked_by_user(post, request.user)
    related_posts = BlogService.get_related_posts(post)
    recent_posts = BlogService.get_recent_posts(exclude_slug=post_slug)

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'recent_posts': recent_posts,
        'is_liked_by_user': is_liked_by_user,
        'likes_count': post.likes.count(),
        'related_posts': related_posts,
    }
    return render(request, 'yoga_app/blog_detail.html', context)


@login_required
@ratelimit(key='ip', rate='5/m', block=True)
def add_blog_comment_view(request, post_slug):
    post = get_object_or_404(BlogPost, slug=post_slug, is_published=True)
    if request.method == 'POST':
        form = BlogCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, 'Your comment has been added!')

            if post.author and post.author != request.user:
                NotificationService.notify_blog_comment(post.author, request.user, post)
            return redirect('blog_detail', post_slug=post.slug)
        else:
            messages.error(request, 'There was an error adding your comment. Please correct the errors.')
    return redirect('blog_detail', post_slug=post_slug)


@login_required
@ratelimit(key='user', rate='30/m', block=True)
def toggle_blog_post_like(request, post_slug):
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, slug=post_slug, is_published=True)
        user = request.user

        liked = False
        with transaction.atomic():
            if user in post.likes.all():
                post.likes.remove(user)
                liked = False
            else:
                post.likes.add(user)
                liked = True
                if post.author and post.author != user:
                    NotificationService.notify_like(post.author, user, 'blog_post', post)
        
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': post.likes.count()
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


# ── Frontend Blog Editor ──────────────────────────────────────────────────────

@login_required
def create_blog_post_view(request):
    """Any authenticated user can submit a blog post draft for review."""
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.is_published = False  # Always draft until staff publishes
            post.save()
            form.save_m2m()  # Save tags
            messages.success(
                request,
                "Your post has been submitted for review. It will appear on the blog once approved by our team."
            )
            return redirect('my_blog_posts')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BlogPostForm()

    return render(request, 'yoga_app/blog_editor.html', {
        'form': form,
        'action': 'create',
        'page_title': 'Write a New Post',
    })


@login_required
def edit_blog_post_view(request, post_slug):
    """Author or staff can edit a post."""
    post = get_object_or_404(BlogPost, slug=post_slug)

    # Only the author or staff can edit
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to edit this post.")
        return redirect('blog_detail', post_slug=post_slug)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            updated = form.save(commit=False)
            # Staff can publish; regular users can only save drafts
            if request.user.is_staff:
                updated.is_published = request.POST.get('is_published') == 'on'
            else:
                updated.is_published = False
            updated.save()
            form.save_m2m()
            messages.success(request, "Post updated successfully.")
            return redirect('blog_detail', post_slug=updated.slug)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BlogPostForm(instance=post)

    return render(request, 'yoga_app/blog_editor.html', {
        'form': form,
        'post': post,
        'action': 'edit',
        'page_title': f'Edit: {post.title}',
        'is_staff': request.user.is_staff,
    })


@login_required
def my_blog_posts_view(request):
    """Dashboard for a user to see all their submitted posts and their status."""
    posts = BlogPost.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'yoga_app/my_blog_posts.html', {'posts': posts})


@login_required
def delete_blog_post_view(request, post_slug):
    """Author or staff can delete a post."""
    post = get_object_or_404(BlogPost, slug=post_slug)
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this post.")
        return redirect('blog_detail', post_slug=post_slug)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted.")
        return redirect('my_blog_posts')
    return render(request, 'yoga_app/blog_delete_confirm.html', {'post': post})
