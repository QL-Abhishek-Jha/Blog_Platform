from rest_framework import serializers
from .models import Topic, Blog, Comment, Notification


class TopicSerializer(serializers.ModelSerializer):
    # shows who created the topic by username instead of user id
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = Topic
        fields = ["id", "name", "slug", "created_by_username", "created_at"]
        read_only_fields = ["id", "slug", "created_by_username", "created_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Topic name cannot be empty.")
        return value.strip()


class BlogListSerializer(serializers.ModelSerializer):
    # lightweight — no content, used in listing pages
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name = serializers.CharField(source="topic.name", read_only=True, default=None)

    class Meta:
        model = Blog
        fields = [
            "id", "title", "slug", "author_username",
            "topic_name", "banner_image", "published_at", "view_count",
        ]
        read_only_fields = fields


class AuthorBlogListSerializer(serializers.ModelSerializer):
    # author's own blog list — includes is_published so they can see draft vs live
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name = serializers.CharField(source="topic.name", read_only=True, default=None)

    class Meta:
        model = Blog
        fields = [
            "id", "title", "slug", "author_username", "topic_name",
            "banner_image", "is_published", "published_at", "view_count",
        ]
        read_only_fields = fields


class AdminBlogListSerializer(serializers.ModelSerializer):
    # admin version — includes is_published so drafts are visible
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name = serializers.CharField(source="topic.name", read_only=True, default=None)

    class Meta:
        model = Blog
        fields = [
            "id", "title", "slug", "author_username", "topic_name",
            "banner_image", "is_published", "published_at", "view_count", "created_at",
        ]
        read_only_fields = fields


class BlogDetailSerializer(serializers.ModelSerializer):
    # used in detail views and as response after create/update
    author_username = serializers.CharField(source="author.username", read_only=True, default=None)
    topic_name = serializers.CharField(source="topic.name", read_only=True, default=None)

    class Meta:
        model = Blog
        fields = [
            "id", "title", "slug", "content", "author_username",
            "topic_name", "banner_image", "published_at", "view_count", "updated_at",
        ]
        read_only_fields = fields


class BlogCreateSerializer(serializers.ModelSerializer):
    # author injected from request.user in the view, not from client
    title = serializers.CharField(
        min_length=3,
        max_length=255,
        error_messages={
            "blank":      "Title is required.",
            "required":   "Title is required.",
            "min_length": "Title must be at least 3 characters.",
            "max_length": "Title cannot exceed 255 characters.",
        }
    )
    content = serializers.CharField(
        min_length=10,
        error_messages={
            "blank":      "Content is required.",
            "required":   "Content is required.",
            "min_length": "Content must be at least 10 characters.",
        }
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        error_messages={
            "required":       "Topic is required.",
            "null":           "Topic cannot be null.",
            "does_not_exist": "Topic does not exist.",
            "incorrect_type": "Invalid topic id.",
        }
    )

    class Meta:
        model = Blog
        fields = ["id", "title", "content", "topic", "banner_image", "is_published"]
        read_only_fields = ["id"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip()


class BlogUpdateSerializer(serializers.ModelSerializer):
    # all fields optional since used with partial=True
    title = serializers.CharField(
        min_length=3,
        max_length=255,
        required=False,
        error_messages={
            "blank":      "Title cannot be empty.",
            "min_length": "Title must be at least 3 characters.",
            "max_length": "Title cannot exceed 255 characters.",
        }
    )
    content = serializers.CharField(
        min_length=10,
        required=False,
        error_messages={
            "blank":      "Content cannot be empty.",
            "min_length": "Content must be at least 10 characters.",
        }
    )
    topic = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        required=False,
        error_messages={
            "does_not_exist": "Topic does not exist.",
            "incorrect_type": "Invalid topic id.",
        }
    )

    class Meta:
        model = Blog
        fields = ["title", "content", "topic", "banner_image", "is_published"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value.strip()


class AdminBlogMigrateTopicSerializer(serializers.Serializer):
    # admin only: move a blog from one topic to another
    new_topic_id = serializers.IntegerField()

    def validate_new_topic_id(self, value):
        if not Topic.objects.filter(id=value).exists():
            raise serializers.ValidationError("Topic does not exist.")
        return value


class CommentSerializer(serializers.ModelSerializer):
    # read only, shows username instead of user id
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "username", "content", "created_at"]
        read_only_fields = fields


class CommentCreateSerializer(serializers.ModelSerializer):
    # blog and user injected by the view, only content comes from client
    content = serializers.CharField(
        min_length=1,
        max_length=1000,
        error_messages={
            "blank":      "Comment cannot be empty.",
            "required":   "Comment is required.",
            "max_length": "Comment cannot exceed 1000 characters.",
        }
    )

    class Meta:
        model = Comment
        fields = ["id", "content"]
        read_only_fields = ["id"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        return value.strip()


class NotificationSerializer(serializers.ModelSerializer):
    # shows blog title and slug instead of blog id
    blog_title = serializers.CharField(source="blog.title", read_only=True)
    blog_slug = serializers.CharField(source="blog.slug", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "blog_title", "blog_slug", "type", "content", "is_read", "created_at"]
        read_only_fields = fields