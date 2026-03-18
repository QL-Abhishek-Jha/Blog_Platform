from apps.users.models import Subscription
from .models import Notification


def send_new_post_notifications(blog):
    # creates a notification record for each subscriber of the author
    subscriptions = Subscription.objects.subscribers_of(author=blog.author)

    notifications = [
        Notification(
            user=sub.subscriber,
            blog=blog,
            type=Notification.TYPE_NEW_POST,
            content=f"{blog.author.username} published a new blog: {blog.title}",
            is_read=False,
        )
        for sub in subscriptions
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)