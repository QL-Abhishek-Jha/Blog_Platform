# Blog Platform API

# Authentication APIs

POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/token/refresh/

# Password APIs

POST /api/auth/change-password/
POST /api/auth/forgot-password/
POST /api/auth/reset-password/<uid>/<token>/

# User APIs

GET /api/users/me/
PATCH /api/users/me/

GET /api/users/authors/<username>/

POST /api/users/subscribe/<username>/
DELETE /api/users/unsubscribe/<username>/

GET /api/users/my-subscriptions/

# Admin APIs

GET /api/admin/users/
GET /api/admin/users/<id>/
PATCH /api/admin/users/<id>/
DELETE /api/admin/users/<id>/

# Superadmin APIs

POST /api/superadmin/create-admin/
