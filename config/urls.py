from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.users.urls import auth_urlpatterns, user_urlpatterns, admin_user_urlpatterns, superadmin_urlpatterns
from apps.blogs.urls import topic_urlpatterns, blog_urlpatterns, author_blog_urlpatterns, admin_blog_urlpatterns, notification_urlpatterns

urlpatterns = [
    # Django Admin Panel
    path("admin/", admin.site.urls),

    # Auth
    path("api/auth/", include(auth_urlpatterns)),

    # User Profiles & Subscriptions
    path("api/users/", include(user_urlpatterns)),

    # Superadmin
    path("api/superadmin/", include(superadmin_urlpatterns)),

    # Admin — User Management
    path("api/admin/users/", include(admin_user_urlpatterns)),

    # Admin — Blog Management
    path("api/admin/blogs/", include(admin_blog_urlpatterns)),

    # Topics
    path("api/blogs/topics/", include(topic_urlpatterns)),

    # Author's own blogs — MUST be BEFORE api/blogs/ to avoid slug conflict
    path("api/blogs/my-blogs/", include(author_blog_urlpatterns)),

    # Blogs (public) — MUST be LAST among blog URLs
    path("api/blogs/", include(blog_urlpatterns)),

    # Notifications
    path("api/notifications/", include(notification_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)