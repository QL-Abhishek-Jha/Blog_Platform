from rest_framework import serializers
from .models import Topic, Blog, Comment, Notification




class TopicSerializer(serializers.ModelSerializer):
    """Full topic serializer — includes created_by info."""
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "name", "slug", "created_by", "created_by_username", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "created_by", "created_by_username", "created_at", "updated_at"]




class BlogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for blog list views. No content field."""
    author_username = serializers.CharField(source="author.username", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = Blog
        fields = [
            "id", "title", "slug", "author", "author_username",
            "topic", "topic_name", "banner_image", "is_published",
            "published_at", "view_count", "created_at",
        ]
        read_only_fields = fields


class BlogDetailSerializer(serializers.ModelSerializer):
    """
    Full blog serializer with content — used for detail views and
    as the response serializer after create/update operations.

    Note: This serializer is read-oriented (most fields are read_only).
    For write operations, use BlogCreateSerializer or BlogUpdateSerializer.
    """
    author_username = serializers.CharField(source="author.username", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = Blog
        fields = [
            "id", "title", "slug", "content", "author", "author_username",
            "topic", "topic_name", "banner_image", "is_published",
            "published_at", "view_count", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "slug", "author", "author_username", "topic_name",
            "published_at", "view_count", "created_at", "updated_at",
        ]


class BlogCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new blog.
    Author is injected from request.user in the view — not passed from client.
    Set is_published=True to publish immediately on creation.
    Set is_published=False (default) to save as draft.
    """

    class Meta:
        model = Blog
        fields = ["id", "title", "content", "topic", "banner_image", "is_published"]
        read_only_fields = ["id"]


class BlogUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for author editing their own blog.
    Always used with partial=True — author can update any subset of fields.
    Setting is_published=True on a draft triggers the publish flow (sets
    published_at and sends subscriber notifications) in the view.
    """

    class Meta:
        model = Blog
        fields = ["title", "content", "topic", "banner_image", "is_published"]


class AdminBlogMigrateTopicSerializer(serializers.Serializer):
    """Admin-only: migrate a blog from one topic to another."""
    new_topic_id = serializers.IntegerField()

    def validate_new_topic_id(self, value):
        if not Topic.objects.filter(id=value).exists():
            raise serializers.ValidationError("Topic does not exist")
        return value


# ---------------------------------------------------------------------------
# COMMENT SERIALIZERS
# ---------------------------------------------------------------------------

class CommentSerializer(serializers.ModelSerializer):
    """Comment read serializer — includes username."""
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "blog", "user", "username", "content", "is_deleted", "created_at", "updated_at"]
        read_only_fields = ["id", "blog", "user", "username", "is_deleted", "created_at", "updated_at"]


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a comment. Only content is required from the client."""

    class Meta:
        model = Comment
        fields = ["id", "content"]
        read_only_fields = ["id"]


# ---------------------------------------------------------------------------
# NOTIFICATION SERIALIZERS
# ---------------------------------------------------------------------------

class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer for subscriber notifications."""
    blog_title = serializers.CharField(source="blog.title", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "blog", "blog_title", "type", "content", "is_read", "created_at"]
        read_only_fields = fields