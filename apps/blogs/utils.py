import logging

from apps.users.models import Subscription
from .models import Notification

logger = logging.getLogger("apps")


def send_new_post_notifications(blog):
    try:
        author_name = blog.author.username if blog.author else "Unknown"

        subscriptions = Subscription.objects.subscribers_of(author=blog.author)

        notifications = [
            Notification(
                user=sub.subscriber,
                blog=blog,
                type=Notification.TYPE_NEW_POST,
                content=f"{author_name} published a new blog: {blog.title}",
                is_read=False,
            )
            for sub in subscriptions
        ]

        if notifications:
            Notification.objects.bulk_create(notifications)

    except Exception as e:
        logger.error(f"Failed to send notifications for blog '{blog.title}': {e}", exc_info=True)