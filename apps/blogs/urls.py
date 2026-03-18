from django.urls import path
from . import views

topic_urlpatterns = [
    path("", views.TopicListCreateView.as_view(), name="topic-list-create"),
    path("<slug:slug>/", views.TopicDetailView.as_view(), name="topic-detail"),
]

blog_urlpatterns = [
    path("", views.PublicBlogListView.as_view(), name="blog-list"),
    path("topic/<slug:slug>/", views.BlogsByTopicView.as_view(), name="blogs-by-topic"),
    path("author/<str:username>/", views.BlogsByAuthorView.as_view(), name="blogs-by-author"),
    path("comments/<int:comment_id>/", views.CommentDeleteView.as_view(), name="comment-delete"),
    path("<slug:slug>/", views.PublicBlogDetailView.as_view(), name="blog-detail"),
    path("<slug:slug>/comments/", views.CommentListCreateView.as_view(), name="blog-comments"),
]

# must be registered before blog_urlpatterns in config/urls.py to avoid slug conflict
author_blog_urlpatterns = [
    path("", views.AuthorBlogListCreateView.as_view(), name="author-blog-list-create"),
    path("<slug:slug>/", views.AuthorBlogDetailView.as_view(), name="author-blog-detail"),
]

admin_blog_urlpatterns = [
    path("", views.AdminBlogListView.as_view(), name="admin-blog-list"),
    path("<int:blog_id>/", views.AdminBlogDetailView.as_view(), name="admin-blog-delete"),
    path("<int:blog_id>/migrate-topic/", views.AdminBlogMigrateTopicView.as_view(), name="admin-blog-migrate-topic"),
]

notification_urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("<int:notification_id>/read/", views.NotificationMarkReadView.as_view(), name="notification-mark-read"),
]