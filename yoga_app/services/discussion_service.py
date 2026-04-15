from django.db import transaction
from django.shortcuts import get_object_or_404
from yoga_app.models import DiscussionTopic, DiscussionPost, Course
from yoga_app.services.notification_service import NotificationService


class DiscussionService:
    @staticmethod
    def get_topics_for_course(course, user):
        return DiscussionTopic.objects.filter(course=course).select_related('user').order_by('-created_at')

    @staticmethod
    def create_topic(course, user, title, content, lesson=None):
        topic = DiscussionTopic.objects.create(
            course=course,
            user=user,
            title=title,
            content=content,
            lesson=lesson,
        )
        return topic

    @staticmethod
    def get_topic_detail(topic_id, course):
        return get_object_or_404(
            DiscussionTopic.objects.select_related('user'),
            id=topic_id,
            course=course
        )

    @staticmethod
    def get_posts_for_topic(topic):
        return topic.posts.all().select_related('user').order_by('created_at')

    @staticmethod
    def create_post(topic, user, content, parent_post=None):
        post = DiscussionPost.objects.create(
            topic=topic,
            user=user,
            content=content,
            parent_post=parent_post,
        )

        if topic.user != user:
            NotificationService.notify_reply(topic.user, user, topic, is_post=False)

        if parent_post and parent_post.user != user:
            NotificationService.notify_reply(parent_post.user, user, topic, is_post=True)

        return post

    @staticmethod
    def can_edit_topic(topic, user):
        return topic.user == user

    @staticmethod
    def can_edit_post(post, user):
        return post.user == user

    @staticmethod
    def delete_topic(topic):
        with transaction.atomic():
            topic.delete()

    @staticmethod
    def delete_post(post):
        with transaction.atomic():
            post.delete()

    @staticmethod
    def toggle_topic_like(topic, user):
        liked = False
        with transaction.atomic():
            if user in topic.likes.all():
                topic.likes.remove(user)
                liked = False
            else:
                topic.likes.add(user)
                liked = True
                NotificationService.notify_like(topic.user, user, 'topic', topic)
        return liked, topic.likes.count()

    @staticmethod
    def toggle_post_like(post, user):
        liked = False
        with transaction.atomic():
            if user in post.likes.all():
                post.likes.remove(user)
                liked = False
            else:
                post.likes.add(user)
                liked = True
                NotificationService.notify_like(post.user, user, 'post', post)
        return liked, post.likes.count()
