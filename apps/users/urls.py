from django.urls import path
from . import views

auth_urlpatterns = [
    path("register/", views.UserRegistrationView.as_view(), name="auth-register"),
    path("login/", views.UserLoginView.as_view(), name="auth-login"),
    path("logout/", views.UserLogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("change-password/", views.ChangePasswordView.as_view(), name="auth-change-password"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="auth-forgot-password"),
    path("reset-password/<str:uid>/<str:token>/", views.ResetPasswordView.as_view(), name="auth-reset-password"),
]

user_urlpatterns = [
    path("me/", views.UserProfileView.as_view(), name="user-profile"),
    path("authors/<str:username>/", views.PublicAuthorProfileView.as_view(), name="author-public-profile"),
    path("subscribe/<str:username>/", views.SubscribeAuthorView.as_view(), name="subscribe-author"),
    path("unsubscribe/<str:username>/", views.UnsubscribeAuthorView.as_view(), name="unsubscribe-author"),
    path("my-subscriptions/", views.MySubscriptionsView.as_view(), name="my-subscriptions"),
]

admin_user_urlpatterns = [
    path("", views.AdminUserListView.as_view(), name="admin-user-list"),
    path("<int:user_id>/", views.AdminUserDetailView.as_view(), name="admin-user-detail"),
]