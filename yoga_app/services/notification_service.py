from django.db import transaction
from django.urls import reverse
from yoga_app.models import Notification


class NotificationService:
    @staticmethod
    def create_notification(recipient, notification_type, message, sender=None, link=''):
        return Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            link=link,
        )

    @staticmethod
    def notify_reply(topic_user, sender, topic, is_post=False):
        if topic_user == sender:
            return None
        message = f"{sender.username} replied to your post in topic: '{topic.title}'" if is_post else f"{sender.username} replied to your topic: '{topic.title}'"
        link = reverse('course_discussion_detail', args=[topic.course.id, topic.id])
        return NotificationService.create_notification(
            recipient=topic_user,
            notification_type='reply',
            message=message,
            sender=sender,
            link=link,
        )

    @staticmethod
    def notify_like(content_owner, liker, content_type, content):
        if content_owner == liker:
            return None

        if content_type == 'topic':
            notif_type = 'like'
            message = f"{liker.username} liked your topic: '{content.title}'"
        elif content_type == 'post':
            notif_type = 'like'
            message = f"{liker.username} liked your post in topic: '{content.topic.title}'"
        elif content_type == 'blog_post':
            notif_type = 'blog_post_like'
            message = f'"{liker.username}" liked your blog post: "{content.title}".'
        else:
            notif_type = 'like'
            message = f"{liker.username} liked your content"

        link = content.get_absolute_url() if hasattr(content, 'get_absolute_url') else ''

        return NotificationService.create_notification(
            recipient=content_owner,
            notification_type=notif_type,
            message=message,
            sender=liker,
            link=link,
        )

    @staticmethod
    def notify_blog_comment(author, commenter, post):
        if author == commenter:
            return None
        link = reverse('blog_detail', args=[post.slug])
        return NotificationService.create_notification(
            recipient=author,
            notification_type='blog_comment',
            message=f'"{commenter.username}" commented on your blog post: "{post.title}".',
            sender=commenter,
            link=link,
        )

    @staticmethod
    def get_user_notifications(user, limit=20):
        return Notification.objects.filter(recipient=user).select_related('sender').order_by('read', '-created_at')[:limit]

    @staticmethod
    def get_notifications_for_api(user):
        notifications_qs = Notification.objects.filter(recipient=user).select_related('sender').order_by('read', '-created_at')
        unread = notifications_qs.filter(read=False)
        recent_read = notifications_qs.filter(read=True)[:5]

        notifications_data = []
        for notif in unread:
            notifications_data.append(NotificationService._serialize_notification(notif))

        for notif in recent_read:
            if notif.id not in [d['id'] for d in notifications_data]:
                notifications_data.append(NotificationService._serialize_notification(notif))

        if unread.exists():
            with transaction.atomic():
                unread.update(read=True)

        return notifications_data

    @staticmethod
    def mark_as_read(user, notification_id=None):
        if notification_id:
            notification = Notification.objects.filter(id=notification_id, recipient=user, read=False).first()
            if notification:
                notification.read = True
                notification.save(update_fields=['read', 'updated_at'])
                return True
        else:
            Notification.objects.filter(recipient=user, read=False).update(read=True)
        return False

    @staticmethod
    def _serialize_notification(notif):
        return {
            'id': notif.id,
            'type': notif.notification_type,
            'message': notif.message,
            'link': notif.link,
            'read': notif.read,
            'created_at': notif.created_at.strftime("%b %d, %Y %I:%M %p"),
            'sender_username': notif.sender.username if notif.sender else None,
        }
