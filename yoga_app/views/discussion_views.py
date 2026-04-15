from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from yoga_app.models import Course, UserProfile, DiscussionTopic, DiscussionPost
from yoga_app.forms import DiscussionTopicForm, DiscussionPostForm
from yoga_app.services import DiscussionService


@login_required
@ratelimit(key='ip', rate='5/m', block=True)
def course_discussion_list_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to access its discussion forum.")
        return redirect('course_detail', course_id=course.id)

    topics = DiscussionService.get_topics_for_course(course, user)

    if request.method == 'POST':
        form = DiscussionTopicForm(request.POST, course=course)
        if form.is_valid():
            topic = DiscussionService.create_topic(
                course=course,
                user=user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                lesson=form.cleaned_data.get('lesson'),
            )
            messages.success(request, f"Discussion topic '{topic.title}' created successfully!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error creating your discussion topic. Please correct the highlighted fields.")
    else:
        form = DiscussionTopicForm(course=course)

    context = {
        'course': course,
        'topics': topics,
        'form': form,
    }
    return render(request, 'yoga_app/course_discussion_list.html', context)


@login_required
@ratelimit(key='ip', rate='10/m', block=True)
def discussion_topic_detail_view(request, course_id, topic_id):
    course = get_object_or_404(Course, id=course_id)
    topic = DiscussionService.get_topic_detail(topic_id, course)
    user = request.user

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to access this discussion topic.")
        return redirect('course_detail', course_id=course.id)

    posts = DiscussionService.get_posts_for_topic(topic)

    if request.method == 'POST':
        form = DiscussionPostForm(request.POST)
        if form.is_valid():
            post = DiscussionService.create_post(
                topic=topic,
                user=user,
                content=form.cleaned_data['content'],
                parent_post=form.cleaned_data.get('parent_post'),
            )
            messages.success(request, "Your reply has been added!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error adding your reply. Please correct the highlighted fields.")
    else:
        form = DiscussionPostForm()

    context = {
        'course': course,
        'topic': topic,
        'posts': posts,
        'form': form,
    }
    return render(request, 'yoga_app/discussion_topic_detail.html', context)


@login_required
def edit_discussion_topic_view(request, course_id, topic_id):
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    user = request.user

    if topic.user != user:
        messages.error(request, "You do not have permission to edit this discussion topic.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to edit this discussion topic.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = DiscussionTopicForm(request.POST, instance=topic, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Discussion topic updated successfully!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error updating your discussion topic. Please correct the highlighted fields.")
    else:
        form = DiscussionTopicForm(instance=topic, course=course)

    context = {
        'course': course,
        'topic': topic,
        'form': form,
        'is_editing': True,
    }
    return render(request, 'yoga_app/discussion_topic_edit.html', context)


@login_required
def delete_discussion_topic_view(request, course_id, topic_id):
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    user = request.user

    if topic.user != user:
        messages.error(request, "You do not have permission to delete this discussion topic.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to delete this discussion topic.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        DiscussionService.delete_topic(topic)
        messages.success(request, f"Discussion topic '{topic.title}' deleted successfully.")
        return redirect('course_discussion_list', course_id=course.id)
    else:
        messages.error(request, "Invalid request method for deleting a discussion topic.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)


@login_required
def edit_discussion_post_view(request, course_id, topic_id, post_id):
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    post = get_object_or_404(DiscussionPost, id=post_id, topic=topic)
    user = request.user

    if post.user != user:
        messages.error(request, "You do not have permission to edit this discussion post.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to edit this discussion post.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = DiscussionPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Discussion post updated successfully!")
            return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
        else:
            messages.error(request, "There was an error updating your discussion post. Please correct the highlighted fields.")
    else:
        form = DiscussionPostForm(instance=post)

    context = {
        'course': course,
        'topic': topic,
        'post': post,
        'form': form,
        'is_editing': True,
    }
    return render(request, 'yoga_app/discussion_post_edit.html', context)


@login_required
def delete_discussion_post_view(request, course_id, topic_id, post_id):
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    post = get_object_or_404(DiscussionPost, id=post_id, topic=topic)
    user = request.user

    if post.user != user:
        messages.error(request, "You do not have permission to delete this discussion post.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)

    user_profile = get_object_or_404(UserProfile, user=user)
    if not user_profile.enrolled_courses.filter(id=course.id).exists():
        messages.error(request, f"You must be enrolled in '{course.title}' to delete this discussion post.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        DiscussionService.delete_post(post)
        messages.success(request, "Discussion post deleted successfully.")
        return redirect('course_discussion_detail', course_id=course.id, topic_id=topic.id)
    else:
        messages.error(request, "Invalid request method for deleting a discussion post.")
        return redirect('course_discussion_detail', course_id=course_id, topic_id=topic.id)


@login_required
@ratelimit(key='user', rate='30/m', block=True)
def toggle_topic_like(request, course_id, topic_id):
    if request.method == 'POST':
        topic = get_object_or_404(DiscussionTopic, id=topic_id, course__id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Not enrolled in course'}, status=403)

        liked, likes_count = DiscussionService.toggle_topic_like(topic, user)
        
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': likes_count
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
@ratelimit(key='user', rate='30/m', block=True)
def toggle_post_like(request, course_id, topic_id, post_id):
    if request.method == 'POST':
        post = get_object_or_404(DiscussionPost, id=post_id, topic__id=topic_id, topic__course__id=course_id)
        user = request.user

        user_profile = get_object_or_404(UserProfile, user=user)
        if not user_profile.enrolled_courses.filter(id=course_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Not enrolled in course'}, status=403)

        liked, likes_count = DiscussionService.toggle_post_like(post, user)
        
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': likes_count
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
