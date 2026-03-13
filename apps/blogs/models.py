from django.db import models
from django.conf import settings
from django.utils.text import slugify

from apps.users.models import TimestampMixin



class TopicManager(models.Manager):
    "Custom manager for Topic model."

    def get_by_slug(self, slug):
        "Return a topic by slug."
        return self.get(slug=slug)

    def created_by_user(self, user):
        "Return all topics created by a specific user."
        return self.filter(created_by=user)


class Topic(TimestampMixin):
    """
    Blog topics/categories.
    Created by admins or authors. Blogs belong to a topic.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="topics_created",
    )

    objects = TopicManager()

    class Meta:
        db_table = "topics"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class BlogManager(models.Manager):
    "Custom manager for Blog model."

    def published(self):
        "Return only published blogs."
        return self.filter(is_published=True)

    def unpublished(self):
        "Return only unpublished (draft) blogs."
        return self.filter(is_published=False)

    def by_author(self, author):
        "Return all blogs by a specific author."
        return self.filter(author=author)

    def by_topic(self, topic):
        "Return all published blogs in a topic."
        return self.filter(topic=topic, is_published=True)


class Blog(TimestampMixin):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blogs",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blogs",
    )
    banner_image = models.ImageField(upload_to="blog_banners/", null=True, blank=True)
    is_published = models.BooleanField(default=False, help_text="False = draft, True = published")
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    objects = BlogManager()

    class Meta:
        db_table = "blogs"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            while Blog.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class CommentManager(models.Manager):
    "Custom manager for Comment model."

    def active(self):
        """Return comments that are not soft-deleted."""
        return self.filter(is_deleted=False)

    def by_blog(self, blog):
        """Return all active comments for a blog."""
        return self.filter(blog=blog, is_deleted=False)

    def by_user(self, user):
        """Return all active comments by a user."""
        return self.filter(user=user, is_deleted=False)


class Comment(TimestampMixin):

    blog = models.ForeignKey(
        Blog,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag")

    objects = CommentManager()

    class Meta:
        db_table = "comments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.blog.title}"


#email serivice is not here for now

class Notification(TimestampMixin):
    """
    Notification for subscribers when an author publishes a new blog.
    Created automatically on blog publish via send_new_post_notifications().
    """
    TYPE_NEW_POST = "new_post"
    TYPE_CHOICES = (
        (TYPE_NEW_POST, "New Post"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="The user (subscriber) who receives this notification",
    )
    blog = models.ForeignKey(
        Blog,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_NEW_POST)
    content = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.content[:50]}"