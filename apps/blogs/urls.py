from django.urls import path
from . import views
# TOPIC ENDPOINTS
# GET  /api/blogs/topics/          — list all topics (public)
# POST /api/blogs/topics/          — create topic (author or admin)
# GET  /api/blogs/topics/<slug>/   — topic detail (public)
# PATCH /api/blogs/topics/<slug>/  — update topic name (admin only)
# DELETE /api/blogs/topics/<slug>/ — delete topic (admin only)
topic_urlpatterns = [
    path("", views.TopicListCreateView.as_view(), name="topic-list-create"),
    path("<slug:slug>/", views.TopicDetailView.as_view(), name="topic-detail"),
]

# PUBLIC BLOG ENDPOINTS
# GET /api/blogs/                         — list all published blogs
# GET /api/blogs/<slug>/                  — single blog detail (increments view count)
# GET /api/blogs/topic/<slug>/            — blogs filtered by topic
# GET /api/blogs/author/<username>/       — blogs filtered by author
# GET /api/blogs/<slug>/comments/         — list comments on a blog
# POST /api/blogs/<slug>/comments/        — add comment (auth required)
# DELETE /api/blogs/comments/<id>/        — delete comment (owner or admin)
blog_urlpatterns = [
    path("", views.PublicBlogListView.as_view(), name="blog-list"),
    path("topic/<slug:slug>/", views.BlogsByTopicView.as_view(), name="blogs-by-topic"),
    path("author/<str:username>/", views.BlogsByAuthorView.as_view(), name="blogs-by-author"),
    path("comments/<int:comment_id>/", views.CommentDeleteView.as_view(), name="comment-delete"),
    path("<slug:slug>/", views.PublicBlogDetailView.as_view(), name="blog-detail"),
    path("<slug:slug>/comments/", views.CommentListCreateView.as_view(), name="blog-comments"),
]

# ---------------------------------------------------------------------------
# AUTHOR — OWN BLOG ENDPOINTS  (must be registered BEFORE blog_urlpatterns
# in config/urls.py to prevent slug conflict with /api/blogs/<slug>/)
# GET  /api/blogs/my-blogs/          — list own blogs (drafts + published)
# POST /api/blogs/my-blogs/          — create blog (draft or published)
# GET  /api/blogs/my-blogs/<slug>/   — own blog detail
# PATCH /api/blogs/my-blogs/<slug>/  — edit own blog (also handles draft → publish)
# ---------------------------------------------------------------------------
author_blog_urlpatterns = [
    path("", views.AuthorBlogListCreateView.as_view(), name="author-blog-list-create"),
    path("<slug:slug>/", views.AuthorBlogDetailView.as_view(), name="author-blog-detail"),
]

# ---------------------------------------------------------------------------
# ADMIN — BLOG MANAGEMENT ENDPOINTS
# GET    /api/admin/blogs/                          — list all blogs (incl. drafts)
# DELETE /api/admin/blogs/<blog_id>/                — hard delete a blog
# PATCH  /api/admin/blogs/<blog_id>/migrate-topic/  — move blog to another topic
# ---------------------------------------------------------------------------
admin_blog_urlpatterns = [
    path("", views.AdminBlogListView.as_view(), name="admin-blog-list"),
    path("<int:blog_id>/", views.AdminBlogDetailView.as_view(), name="admin-blog-delete"),
    path("<int:blog_id>/migrate-topic/", views.AdminBlogMigrateTopicView.as_view(), name="admin-blog-migrate-topic"),
]

# ---------------------------------------------------------------------------
# NOTIFICATION ENDPOINTS
# GET   /api/notifications/                    — list own notifications
# PATCH /api/notifications/<id>/read/          — mark notification as read
# ---------------------------------------------------------------------------
notification_urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("<int:notification_id>/read/", views.NotificationMarkReadView.as_view(), name="notification-mark-read"),
]