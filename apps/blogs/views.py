import logging

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

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
from core.permissions import IsAuthorUser, IsAdminUser, IsAuthorOrAdminUser
from core.pagination import StandardPagination
from core.messages import MSG
from .utils import send_new_post_notifications


logger = logging.getLogger("apps")


# ── Pagination Mixin ──────────────────────────────────────────────────────────
# This mixin gives any APIView the same paginate_queryset / get_paginated_response
# helpers that generic views (ListAPIView) have built-in.
# Just inherit it before APIView: class MyView(PaginationMixin, APIView)
class PaginationMixin:
    pagination_class = StandardPagination

    @property
    def paginator(self):
        "create one paginator instance and reuse it for the whole request"
        if not hasattr(self, "_paginator"):
            self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        "slices the queryset down to the current page only"
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        "wraps serialized data in the standard pagination envelope"
        return self.paginator.get_paginated_response(data)


# ── Topic Views ───────────────────────────────────────────────────────────────

class TopicListCreateView(PaginationMixin, APIView):
    "GET is public and paginated, POST requires author or admin role"

    def get_authenticators(self):
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsAuthorOrAdminUser()]

    def get(self, request):
        "return all topics paginated so the client can scroll through them"
        try:
            topics = Topic.objects.all()
            page = self.paginate_queryset(topics)
            if page is not None:
                serializer = TopicSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            # fallback when queryset is empty or pagination is disabled
            serializer = TopicSerializer(topics, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch topics: {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        "create a new topic, saving who created it"
        serializer = TopicSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TopicDetailView(APIView):
    "GET is public, PATCH/DELETE requires admin role"

    def get_authenticators(self):
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def _get_topic(self, slug):
        "look up a topic by its slug, returns None if not found"
        return Topic.objects.filter(slug=slug).first()

    def get(self, request, slug):
        topic = self._get_topic(slug)
        if not topic:
            return Response({"error": MSG.ERR_TOPIC_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        return Response(TopicSerializer(topic).data, status=status.HTTP_200_OK)

    def patch(self, request, slug):
        topic = self._get_topic(slug)
        if not topic:
            return Response({"error": MSG.ERR_TOPIC_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        serializer = TopicSerializer(topic, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(
            {"message": MSG.TOPIC_UPDATED, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, slug):
        topic = self._get_topic(slug)
        if not topic:
            return Response({"error": MSG.ERR_TOPIC_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        # check first so we return a readable error before Django raises ProtectedError
        if Blog.objects.filter(topic=topic).exists():
            return Response({"error": MSG.ERR_TOPIC_HAS_BLOGS}, status=status.HTTP_400_BAD_REQUEST)
        topic.delete()
        return Response({"message": MSG.TOPIC_DELETED}, status=status.HTTP_200_OK)


# ── Public Blog Views ─────────────────────────────────────────────────────────

class PublicBlogListView(PaginationMixin, APIView):
    "anyone can browse published blogs — paginated"
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            blogs = Blog.objects.published().select_related("author", "topic")
            page = self.paginate_queryset(blogs)
            if page is not None:
                serializer = BlogListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = BlogListSerializer(blogs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch blog list: {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PublicBlogDetailView(APIView):
    "increment view_count each time someone opens a blog"
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            blog = Blog.objects.filter(slug=slug, is_published=True).select_related("author", "topic").first()
            if not blog:
                return Response({"error": MSG.ERR_BLOG_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            blog.view_count += 1
            blog.save(update_fields=["view_count"])
            return Response(BlogDetailSerializer(blog).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch blog detail for slug '{slug}': {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlogsByTopicView(PaginationMixin, APIView):
    "returns paginated list of published blogs under a given topic slug"
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            topic = Topic.objects.filter(slug=slug).first()
            if not topic:
                return Response({"error": MSG.ERR_TOPIC_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            blogs = Blog.objects.by_topic(topic).select_related("author", "topic")
            page = self.paginate_queryset(blogs)
            if page is not None:
                serializer = BlogListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = BlogListSerializer(blogs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch blogs by topic '{slug}': {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlogsByAuthorView(PaginationMixin, APIView):
    "returns paginated list of published blogs written by a specific author"
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            from apps.users.models import User
            author = User.objects.filter(username=username, role="author", is_active=True).first()
            if not author:
                return Response({"error": MSG.ERR_AUTHOR_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            blogs = Blog.objects.published().filter(author=author).select_related("author", "topic")
            page = self.paginate_queryset(blogs)
            if page is not None:
                serializer = BlogListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = BlogListSerializer(blogs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch blogs by author '{username}': {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Author Blog Views ─────────────────────────────────────────────────────────

class AuthorBlogListCreateView(PaginationMixin, APIView):
    "author sees all their own blogs (draft + published), paginated"
    permission_classes = [IsAuthenticated, IsAuthorUser]

    def get(self, request):
        try:
            blogs = Blog.objects.by_author(request.user).select_related("topic")
            page = self.paginate_queryset(blogs)
            if page is not None:
                serializer = AuthorBlogListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = AuthorBlogListSerializer(blogs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch author blog list for user '{request.user.email}': {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        "create a new blog; if published immediately, send notifications to subscribers"
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
    "author can view or edit only their own blog"
    permission_classes = [IsAuthenticated, IsAuthorUser]

    def _get_blog(self, slug, author):
        "only return the blog if it belongs to the current author"
        return Blog.objects.filter(slug=slug, author=author).select_related("topic").first()

    def get(self, request, slug):
        blog = self._get_blog(slug, request.user)
        if not blog:
            return Response({"error": MSG.ERR_BLOG_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        return Response(BlogDetailSerializer(blog).data, status=status.HTTP_200_OK)

    def patch(self, request, slug):
        try:
            blog = self._get_blog(slug, request.user)
            if not blog:
                return Response({"error": MSG.ERR_BLOG_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            was_published = blog.is_published
            serializer = BlogUpdateSerializer(blog, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            is_now_published = serializer.validated_data.get("is_published", blog.is_published)
            if not was_published and is_now_published:
                # blog is being published for first time — stamp published_at and notify subscribers
                serializer.save(published_at=timezone.now())
                blog.refresh_from_db()
                send_new_post_notifications(blog)
            elif was_published and not is_now_published:
                # blog is being unpublished — clear the published_at timestamp
                serializer.save(published_at=None)
                blog.refresh_from_db()
            else:
                serializer.save()
                blog.refresh_from_db()
            return Response(BlogDetailSerializer(blog).data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to update blog '{slug}' for user '{request.user.email}': {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Admin Blog Views ──────────────────────────────────────────────────────────

class AdminBlogListView(PaginationMixin, APIView):
    "admin sees ALL blogs (published + drafts), paginated"
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            blogs = Blog.objects.all().select_related("author", "topic")
            page = self.paginate_queryset(blogs)
            if page is not None:
                serializer = AdminBlogListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = AdminBlogListSerializer(blogs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Admin failed to fetch blog list: {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminBlogDetailView(APIView):
    "admin can hard-delete any blog by its id"
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, blog_id):
        blog = Blog.objects.filter(id=blog_id).first()
        if not blog:
            return Response({"error": MSG.ERR_BLOG_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        blog.delete()
        # BUG FIX: original code had hasattr(MSG, 'BLOG_DELETED') guard which is wrong —
        # MSG.BLOG_DELETED does not exist in messages.py so it always fell to the fallback string.
        # Removed the guard and use a direct string message.
        return Response({"message": "Blog deleted successfully"}, status=status.HTTP_200_OK)


class AdminBlogMigrateTopicView(APIView):
    "admin can move a blog from one topic to another"
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, blog_id):
        blog = Blog.objects.filter(id=blog_id).first()
        if not blog:
            return Response({"error": MSG.ERR_BLOG_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminBlogMigrateTopicSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        new_topic = Topic.objects.filter(id=serializer.validated_data["new_topic_id"]).first()
        if not new_topic:
            return Response({"error": MSG.ERR_TOPIC_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        old_topic_name = blog.topic.name if blog.topic else "None"
        blog.topic = new_topic
        blog.save(update_fields=["topic"])
        return Response(
            {
                "message": MSG.BLOG_MIGRATED,
                "blog_id": blog.id,
                "old_topic": old_topic_name,
                "new_topic": new_topic.name,
            },
            status=status.HTTP_200_OK,
        )


# ── Comment Views ─────────────────────────────────────────────────────────────

class CommentListCreateView(PaginationMixin, APIView):
    "GET is public (paginated comments), POST requires login"

    def get_authenticators(self):
        if self.request.method == "GET":
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, slug):
        "returns non-deleted comments for a blog, newest first, paginated"
        try:
            blog = Blog.objects.filter(slug=slug, is_published=True).first()
            if not blog:
                return Response({"error": MSG.ERR_BLOG_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            comments = Comment.objects.by_blog(blog).select_related("user")
            page = self.paginate_queryset(comments)
            if page is not None:
                serializer = CommentSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch comments for blog '{slug}': {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, slug):
        blog = Blog.objects.filter(slug=slug, is_published=True).first()
        if not blog:
            return Response({"error": MSG.ERR_BLOG_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        comment = serializer.save(blog=blog, user=request.user)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDeleteView(APIView):
    "soft-delete: sets is_deleted=True instead of removing the row from DB"
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        comment = Comment.objects.filter(id=comment_id, is_deleted=False).first()
        if not comment:
            return Response({"error": MSG.ERR_COMMENT_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        # only the comment owner or an admin is allowed to delete a comment
        if comment.user != request.user and getattr(request.user, "role", None) != "admin":
            return Response({"error": MSG.ERR_PERMISSION_DENIED}, status=status.HTTP_403_FORBIDDEN)
        comment.is_deleted = True
        comment.save(update_fields=["is_deleted"])
        return Response({"message": MSG.COMMENT_DELETED}, status=status.HTTP_200_OK)


#Notification Views
class NotificationListView(PaginationMixin, APIView):
    "returns the logged-in user's notifications, newest first, paginated"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            notifications = Notification.objects.filter(user=request.user)
            page = self.paginate_queryset(notifications)
            if page is not None:
                serializer = NotificationSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = NotificationSerializer(notifications, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to fetch notifications for user '{request.user.email}': {e}", exc_info=True)
            return Response({"error": MSG.ERR_SOMETHING_WRONG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationMarkReadView(APIView):
    "marks a single notification as read for the currently logged-in user"
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        notification = Notification.objects.filter(id=notification_id, user=request.user).first()
        if not notification:
            return Response({"error": MSG.ERR_NOTIF_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"message": MSG.NOTIFICATION_READ}, status=status.HTTP_200_OK)