from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.users.urls import auth_urlpatterns, user_urlpatterns, admin_user_urlpatterns
from apps.blogs.urls import topic_urlpatterns, blog_urlpatterns, author_blog_urlpatterns, admin_blog_urlpatterns, notification_urlpatterns


    
api_urlpatterns = [
    
    path("auth/",           include(auth_urlpatterns)),
    path("users/",          include(user_urlpatterns)),
    path("admin/users/",    include(admin_user_urlpatterns)),
    path("admin/blogs/",    include(admin_blog_urlpatterns)),
    path("blogs/topics/",   include(topic_urlpatterns)),
    path("blogs/my-blogs/", include(author_blog_urlpatterns)),
    path("blogs/",          include(blog_urlpatterns)),
    path("notifications/",  include(notification_urlpatterns)),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/",   include(api_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)