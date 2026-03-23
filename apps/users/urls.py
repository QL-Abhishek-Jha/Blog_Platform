from django.urls import path, include
from . import views

auth_urlpatterns = [
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token-refresh"),
    path("password/change/", views.ChangePasswordView.as_view(), name="password-change"),
    path("password/forgot/", views.ForgotPasswordView.as_view(), name="password-forgot"),
    path("password/reset/<str:uid>/<str:token>/", views.ResetPasswordView.as_view(), name="password-reset"),
]

profile_urlpatterns = [
    path("me/", views.UserProfileView.as_view(), name="me"),
    path("authors/<str:username>/", views.PublicAuthorProfileView.as_view(), name="author-profile"),
    path("authors/<str:username>/subscribe/", views.SubscribeAuthorView.as_view(), name="author-subscribe"),
    path("authors/<str:username>/unsubscribe/", views.UnsubscribeAuthorView.as_view(), name="author-unsubscribe"),
    path("subscriptions/", views.MySubscriptionsView.as_view(), name="my-subscriptions"),
]

admin_urlpatterns = [
    path("", views.AdminUserListView.as_view(), name="admin-user-list"),
    path("<int:user_id>/", views.AdminUserDetailView.as_view(), name="admin-user-detail"),
]

users_urlpatterns = [
    path("auth/", include(auth_urlpatterns)),
    path("users/", include(profile_urlpatterns)),
    path("users/admin/", include(admin_urlpatterns)),
]