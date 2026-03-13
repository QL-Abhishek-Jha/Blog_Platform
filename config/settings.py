from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from .env file
load_dotenv(BASE_DIR / ".env")


# SECURITY SETTINGS

# Secret key used for cryptographic signing
SECRET_KEY = os.getenv("SECRET_KEY")

# Debug mode (True in development, False in production)
DEBUG = os.getenv("DEBUG") == "True"

# Hosts allowed to access the project
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# APPLICATIONS

# Default Django applications
DJANGO_APPS = [
    "django.contrib.admin",          # Django admin panel
    "django.contrib.auth",           # Authentication system
    "django.contrib.contenttypes",   # Content types framework
    "django.contrib.sessions",       # Session management
    "django.contrib.messages",       # Messaging framework
    "django.contrib.staticfiles",    # Static files support
    "django_extensions",             # Extra developer utilities
]

# Third party packages
THIRD_PARTY_APPS = [
    "rest_framework",                        # Django REST Framework
    "rest_framework_simplejwt",              # JWT authentication
    "rest_framework_simplejwt.token_blacklist",  # Token blacklist support
    "corsheaders",                           # Handle CORS requests
]

# Local apps created in this project
LOCAL_APPS = [
    "apps.users",     # Users app
    "apps.blogs",     # Blogs app
]

# Combine all apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# MIDDLEWARE

# Middleware processes request and response globally
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",          # Handles CORS
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",      # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# URL AND WSGI CONFIGURATION

# Root URL configuration file
ROOT_URLCONF = "config.urls"

# WSGI application
WSGI_APPLICATION = "config.wsgi.application"


# TEMPLATES

# Template settings used by Django
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # Custom template folder
        "APP_DIRS": True,                   # Load templates inside apps
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# DATABASE

# MySQL database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",  # Using MySQL database
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"
        },
    }
}


# CUSTOM USER MODEL

# Using custom user model instead of Django default
AUTH_USER_MODEL = "users.User"


# PASSWORD VALIDATORS

# These validators improve password security
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]


# INTERNATIONALIZATION

# Default language
LANGUAGE_CODE = "en-us"

# Time zone
TIME_ZONE = "UTC"

# Enable internationalization
USE_I18N = True

# Enable timezone support
USE_TZ = True


# STATIC FILES

# URL for static files (CSS, JS)
STATIC_URL = "/static/"

# Folder where static files will be collected
STATIC_ROOT = BASE_DIR / "staticfiles"


# MEDIA FILES

# URL for media files (uploads)
MEDIA_URL = "/media/"

# Folder where uploaded files are stored
MEDIA_ROOT = BASE_DIR / "media"


# DEFAULT PRIMARY KEY

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# DJANGO REST FRAMEWORK SETTINGS

REST_FRAMEWORK = {
    # JWT authentication used globally
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],

    # Default permission (user must be authenticated)
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],

    # Response format
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],

    # Pagination settings
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}


# SIMPLE JWT SETTINGS

SIMPLE_JWT = {
    # Access token lifetime
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=55),

    # Refresh token lifetime
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),

    # Generate new refresh token after use
    "ROTATE_REFRESH_TOKENS": True,

    # Blacklist old refresh tokens
    "BLACKLIST_AFTER_ROTATION": True,

    # Update last login time
    "UPDATE_LAST_LOGIN": True,

    # Algorithm used to sign tokens
    "ALGORITHM": "HS256",

    # Signing key for tokens
    "SIGNING_KEY": SECRET_KEY,

    # Authorization header format
    "AUTH_HEADER_TYPES": ("Bearer",),

    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",

    # Field used as user identifier
    "USER_ID_FIELD": "id",

    "USER_ID_CLAIM": "user_id",

    # Token serializers
    "TOKEN_OBTAIN_PAIR_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
}


# CORS SETTINGS

# Allowed frontend URLs
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Allow cookies/auth headers in cross-origin requests
CORS_ALLOW_CREDENTIALS = True