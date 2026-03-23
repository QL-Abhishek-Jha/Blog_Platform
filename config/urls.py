from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.users.urls import users_urlpatterns
from apps.blogs.urls import blogs_urlpatterns


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/",   include(users_urlpatterns)),
    path("api/", include(blogs_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)