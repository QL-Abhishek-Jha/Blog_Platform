from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import F

from .models import Topic, Blog, Comment, Notification
from .serializers import (
    TopicSerializer,
    BlogListSerializer,
    AuthorBlogListSerializer,
    AdminBlogListSerializer,
    BlogDetailSerializer,
    BlogCreateSerializer,
    BlogUpdateSerializer,
    AdminBlogMigrateTopicSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    NotificationSerializer,
)
from apps.users.permissions import IsAuthorUser, IsAdminUser, IsAuthorOrAdminUser
from .utils import send_new_post_notifications


class TopicListCreateView(APIView):
    # GET is public, POST requires author or admin

    def get_authenticators(self):
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdminUser()]

    def get(self, request):
        topics = Topic.objects.all()
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TopicSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TopicDetailView(APIView):
    # GET is public, PATCH and DELETE require admin

    def get_authenticators(self):
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def _get_topic(self, slug):
        return Topic.objects.filter(slug=slug).first()

    def get(self, request, slug):
        topic = self._get_topic(slug)
        if not topic:
            return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TopicSerializer(topic)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, slug):
        topic = self._get_topic(slug)
        if not topic:
            return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = TopicSerializer(topic, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, slug):
        topic = self._get_topic(slug)
        if not topic:
            return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
        if Blog.objects.filter(topic=topic).exists():
            return Response(
                {"error": "Cannot delete topic. Move or delete blogs under this topic first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        topic.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicBlogListView(APIView):
    # public — no auth required, only published blogs

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        blogs = Blog.objects.published().select_related("author", "topic")
        serializer = BlogListSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicBlogDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug):
        blog = Blog.objects.filter(slug=slug, is_published=True).select_related("author", "topic").first()
        if not blog:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        
        Blog.objects.filter(pk=blog.pk).update(view_count=F("view_count") + 1)
        blog.refresh_from_db()
        
        serializer = BlogDetailSerializer(blog)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BlogsByTopicView(APIView):
    # public — all published blogs under a specific topic

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug):
        topic = Topic.objects.filter(slug=slug).first()
        if not topic:
            return Response({"error": "Topic not found"}, status=status.HTTP_404_NOT_FOUND)
        blogs = Blog.objects.by_topic(topic).select_related("author", "topic")
        serializer = BlogListSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BlogsByAuthorView(APIView):
    # public — all published blogs by a specific author

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, username):
        from apps.users.models import User
        author = User.objects.filter(username=username, role="author", is_active=True).first()
        if not author:
            return Response({"error": "Author not found"}, status=status.HTTP_404_NOT_FOUND)
        blogs = Blog.objects.published().filter(author=author).select_related("author", "topic")
        serializer = BlogListSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AuthorBlogListCreateView(APIView):
    # author only — list own blogs (drafts + published) or create new blog

    permission_classes = [IsAuthenticated, IsAuthorUser]

    def get(self, request):
        blogs = Blog.objects.by_author(request.user).select_related("topic")
        serializer = AuthorBlogListSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BlogCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        is_published = serializer.validated_data.get("is_published", False)
        blog = serializer.save(
            author=request.user,
            published_at=timezone.now() if is_published else None,
        )
        if is_published:
            send_new_post_notifications(blog)
        return Response(BlogDetailSerializer(blog).data, status=status.HTTP_201_CREATED)


class AuthorBlogDetailView(APIView):
    # author only — view, edit, or publish their own blog

    permission_classes = [IsAuthenticated, IsAuthorUser]

    def _get_blog(self, slug, author):
        return Blog.objects.filter(slug=slug, author=author).select_related("topic").first()

    def get(self, request, slug):
        blog = self._get_blog(slug, request.user)
        if not blog:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BlogDetailSerializer(blog)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, slug):
        blog = self._get_blog(slug, request.user)
        if not blog:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        was_published = blog.is_published
        serializer = BlogUpdateSerializer(blog, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        is_now_published = serializer.validated_data.get("is_published", blog.is_published)
        if not was_published and is_now_published:
            # draft going live — set published_at and notify subscribers
            serializer.save(published_at=timezone.now())
            blog.refresh_from_db()
            send_new_post_notifications(blog)
        elif was_published and not is_now_published:
            # going back to draft — clear published_at
            serializer.save(published_at=None)
            blog.refresh_from_db()
        else:
            serializer.save()
            blog.refresh_from_db()
        return Response(BlogDetailSerializer(blog).data, status=status.HTTP_200_OK)


class AdminBlogListView(APIView):
    # admin only — shows all blogs including drafts

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        blogs = Blog.objects.all().select_related("author", "topic")
        serializer = AdminBlogListSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminBlogDetailView(APIView):
    # admin only — hard delete a blog

    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, blog_id):
        blog = Blog.objects.filter(id=blog_id).first()
        if not blog:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        blog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminBlogMigrateTopicView(APIView):
    # admin only — move a blog to a different topic

    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, blog_id):
        blog = Blog.objects.filter(id=blog_id).first()
        if not blog:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminBlogMigrateTopicSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        new_topic = Topic.objects.get(id=serializer.validated_data["new_topic_id"])
        old_topic_name = blog.topic.name if blog.topic else "None"
        blog.topic = new_topic
        blog.save(update_fields=["topic"])
        return Response(
            {
                "message": f"Blog migrated from '{old_topic_name}' to '{new_topic.name}'",
                "blog_id": blog.id,
                "new_topic": new_topic.name,
            },
            status=status.HTTP_200_OK,
        )


class CommentListCreateView(APIView):
    # GET is public, POST requires login

    def get_authenticators(self):
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, slug):
        blog = Blog.objects.filter(slug=slug, is_published=True).first()
        if not blog:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        comments = Comment.objects.by_blog(blog).select_related("user")
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, slug):
        blog = Blog.objects.filter(slug=slug, is_published=True).first()
        if not blog:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save(blog=blog, user=request.user)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    # owner or admin can delete a comment (soft delete)

    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        comment = Comment.objects.filter(id=comment_id, is_deleted=False).first()
        if not comment:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        if comment.user != request.user and request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        comment.is_deleted = True
        comment.save(update_fields=["is_deleted"])
        return Response({"message": "Comment deleted"}, status=status.HTTP_200_OK)


class NotificationListView(APIView):
    # logged in user sees their own notifications

    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationMarkReadView(APIView):
    # marks a single notification as read

    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        notification = Notification.objects.filter(id=notification_id, user=request.user).first()
        if not notification:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)