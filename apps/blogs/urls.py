from django.urls import path
from . import views

"all blog app routes — mounted at api/blogs/ in config/urls.py"

blogs_urlpatterns = [

    #Topics 
    path("topics/", views.TopicListCreateView.as_view(),name="topic-list"),
    path("topics/<slug:slug>/", views.TopicDetailView.as_view(), name="topic-detail"),

    #Public blogs 
    path("",views.PublicBlogListView.as_view(),name="blog-list"),
    path("<slug:slug>/", views.PublicBlogDetailView.as_view(),       name="blog-detail"),
    path("topic/<slug:slug>/",views.BlogsByTopicView.as_view(),name="blogs-by-topic"),
    path("author/<str:username>/",views.BlogsByAuthorView.as_view(),name="blogs-by-author"),

    #Comments
    path("<slug:slug>/comments/",views.CommentListCreateView.as_view(),name="blog-comments"),
    path("comments/<int:comment_id>/",views.CommentDeleteView.as_view(),name="comment-delete"),

    #Author(own blogs)
    path("mine/",views.AuthorBlogListCreateView.as_view(),name="my-blogs"),
    path("mine/<slug:slug>/",views.AuthorBlogDetailView.as_view(),name="my-blog-detail"),

    #Admin
    path("admin/",views.AdminBlogListView.as_view(),name="admin-blog-list"),
    path("admin/<int:blog_id>/",views.AdminBlogDetailView.as_view(),name="admin-blog-detail"),
    path("admin/<int:blog_id>/topic/",views.AdminBlogMigrateTopicView.as_view(),name="admin-blog-topic"),

    #Notifications
    path("notifs/",views.NotificationListView.as_view(),name="notif-list"),
    path("notifs/<int:notification_id>/read/", views.NotificationMarkReadView.as_view(),   name="notif-read"),
]