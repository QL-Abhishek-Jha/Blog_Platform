from rest_framework import serializers
from .models import Topic, Blog, Comment, Notification


class TopicSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model            = Topic
        fields           = ["id", "name", "slug", "created_by_username", "created_at"]
        read_only_fields = ["id", "slug", "created_by_username", "created_at"]

    def validate(self, data):
        name = data.get("name", "")
        if not name.strip():
            raise serializers.ValidationError({"name": "Topic name cannot be empty."})
        data["name"] = name.strip()
        return data


class BlogListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name      = serializers.CharField(source="topic.name",      read_only=True, default=None)

    class Meta:
        model            = Blog
        fields           = ["id", "title", "slug", "author_username", "topic_name", "banner_image", "published_at", "view_count"]
        read_only_fields = ["id", "title", "slug", "author_username", "topic_name", "banner_image", "published_at", "view_count"]


class AuthorBlogListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name      = serializers.CharField(source="topic.name",      read_only=True, default=None)

    class Meta:
        model            = Blog
        fields           = ["id", "title", "slug", "author_username", "topic_name", "banner_image", "is_published", "published_at", "view_count"]
        read_only_fields = ["id", "title", "slug", "author_username", "topic_name", "banner_image", "is_published", "published_at", "view_count"]


class AdminBlogListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name      = serializers.CharField(source="topic.name",      read_only=True, default=None)

    class Meta:
        model            = Blog
        fields           = ["id", "title", "slug", "author_username", "topic_name", "banner_image", "is_published", "published_at", "view_count", "created_at"]
        read_only_fields = ["id", "title", "slug", "author_username", "topic_name", "banner_image", "is_published", "published_at", "view_count", "created_at"]


class BlogDetailSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name      = serializers.CharField(source="topic.name",      read_only=True, default=None)

    class Meta:
        model            = Blog
        fields           = ["id", "title", "slug", "content", "author_username", "topic_name", "banner_image", "published_at", "view_count", "updated_at"]
        read_only_fields = ["id", "title", "slug", "content", "author_username", "topic_name", "banner_image", "published_at", "view_count", "updated_at"]


class BlogCreateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        min_length=3,
        max_length=255,
        error_messages={
            "blank":      "Title is required.",
            "required":   "Title is required.",
            "min_length": "Title must be at least 3 characters.",
            "max_length": "Title cannot exceed 255 characters.",
        },
    )
    content = serializers.CharField(
        min_length=10,
        error_messages={
            "blank":      "Content is required.",
            "required":   "Content is required.",
            "min_length": "Content must be at least 10 characters.",
        },
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        error_messages={
            "required":       "Topic is required.",
            "null":           "Topic cannot be null.",
            "does_not_exist": "Topic does not exist.",
            "incorrect_type": "Invalid topic id.",
        },
    )

    class Meta:
        model            = Blog
        fields           = ["id", "title", "content", "topic", "banner_image", "is_published"]
        read_only_fields = ["id"]

    def validate(self, data):
        errors = {}

        title   = data.get("title", "")
        content = data.get("content", "")

        if title and not title.strip():
            errors["title"] = "Title cannot be empty."

        if content and not content.strip():
            errors["content"] = "Content cannot be empty."

        if errors:
            raise serializers.ValidationError(errors)

        if title:
            data["title"] = title.strip()
        if content:
            data["content"] = content.strip()

        return data


class BlogUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        min_length=3,
        max_length=255,
        required=False,
        error_messages={
            "blank":      "Title cannot be empty.",
            "min_length": "Title must be at least 3 characters.",
            "max_length": "Title cannot exceed 255 characters.",
        },
    )
    content = serializers.CharField(
        min_length=10,
        required=False,
        error_messages={
            "blank":      "Content cannot be empty.",
            "min_length": "Content must be at least 10 characters.",
        },
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        required=False,
        error_messages={
            "does_not_exist": "Topic does not exist.",
            "incorrect_type": "Invalid topic id.",
        },
    )

    class Meta:
        model  = Blog
        fields = ["title", "content", "topic", "banner_image", "is_published"]

    def validate(self, data):
        errors = {}

        title   = data.get("title")
        content = data.get("content")

        if title is not None and not title.strip():
            errors["title"] = "Title cannot be empty."

        if content is not None and not content.strip():
            errors["content"] = "Content cannot be empty."

        if errors:
            raise serializers.ValidationError(errors)

        if title is not None:
            data["title"] = title.strip()
        if content is not None:
            data["content"] = content.strip()

        return data


class AdminBlogMigrateTopicSerializer(serializers.Serializer):
    new_topic_id = serializers.IntegerField()

    def validate(self, data):
        new_topic_id = data.get("new_topic_id")

        if not Topic.objects.filter(id=new_topic_id).exists():
            raise serializers.ValidationError({"new_topic_id": "Topic does not exist."})

        return data


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model            = Comment
        fields           = ["id", "username", "content", "created_at"]
        read_only_fields = ["id", "username", "content", "created_at"]


class CommentCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(
        min_length=1,
        max_length=1000,
        error_messages={
            "blank":      "Comment cannot be empty.",
            "required":   "Comment is required.",
            "max_length": "Comment cannot exceed 1000 characters.",
        },
    )

    class Meta:
        model            = Comment
        fields           = ["id", "content"]
        read_only_fields = ["id"]

    def validate(self, data):
        content = data.get("content", "")

        if not content.strip():
            raise serializers.ValidationError({"content": "Comment cannot be empty."})

        data["content"] = content.strip()
        return data


class NotificationSerializer(serializers.ModelSerializer):
    blog_title = serializers.CharField(source="blog.title", read_only=True, default=None)
    blog_slug  = serializers.CharField(source="blog.slug",  read_only=True, default=None)

    class Meta:
        model            = Notification
        fields           = ["id", "blog_title", "blog_slug", "type", "content", "is_read", "created_at"]
        read_only_fields = ["id", "blog_title", "blog_slug", "type", "content", "is_read", "created_at"]