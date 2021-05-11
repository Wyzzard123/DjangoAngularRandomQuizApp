"""
Django settings for DjangoRandomQuiz project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
from _socket import gethostname
from pathlib import Path
import os
from random import SystemRandom

from environ import Env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
env = Env()
if Path(BASE_DIR, 'config', '.env').is_file():
    env.read_env(str(Path(BASE_DIR, 'config', '.env')))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    'SECRET_KEY',
    str,
    ''.join([SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(50)]),
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = tuple(env('ALLOWED_HOSTS', list, ['localhost', '127.0.0.1', gethostname(), '*']))

# For now, allow CORS requests from all domains. TODO - Change this.
CORS_ORIGIN_ALLOW_ALL = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'quiz.apps.QuizConfig',
    'oauth2_provider',
    'corsheaders',
    # 'restless',
    'rest_framework',
    # 'rest_framework.authtoken',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware"
]

# Use the oauth toolkit's oauth tokens instead of the django rest framework tokens.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ]
}

# Authentication configuration
AUTHENTICATION_BACKENDS = [
    # See https://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_03.html
    #  However, it seems like this backend isn't required for the api to function
    #  See https://django-oauth-toolkit.readthedocs.io/en/latest/rest-framework/getting_started.html where the backend
    #  is not set.
    # Note that if we use this backend, it must be placed before the django modelbackend. The modelbackend is required
    #  to get into the admin page.
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'DjangoRandomQuiz.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DjangoRandomQuiz.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# Databases configuration
DATABASES = {
    'default': env.db(default='sqlite:////{}'.format(os.path.join(BASE_DIR, 'db.sqlite3'))),
}

CLIENT_ID = env('CLIENT_ID', str, 'ABCDEFG')

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = env(
        'STATIC_URL',
        cast=str,
        default='/static/'
)
