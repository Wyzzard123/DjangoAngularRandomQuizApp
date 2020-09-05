"""DjangoRandomQuiz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from quiz.api import TopicResource
from rest_framework import routers

from quiz.views import TopicAPIView, QuestionAPIView, AnswerAPIView, UserCreateView, QuestionAnswerAPIView, \
    GenerateQuizAPIView, CheckQuizAnswersAPIView

router = routers.DefaultRouter()
# We need to pass in basename as we have not set a queryset (we used get_queryset instead) in the TopicAPIView.
router.register('topics', TopicAPIView, basename='topic')
router.register('questions', QuestionAPIView, basename='question')
router.register('answers', AnswerAPIView, basename='answer')
# create_qa creates a Question, Answers and attaches the question to a topic.
router.register('qna', QuestionAnswerAPIView, basename='qna')
router.register('generate_quiz', GenerateQuizAPIView, basename='generate_quiz')
router.register('attempt_quiz', CheckQuizAnswersAPIView, basename='attempt_quiz')

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/topics/', include(TopicResource.urls())),
    # Oauth links
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # The obtain_auth_token view will return a JSON response when valid username and password fields are POSTed to the
    # view using form data or JSON:
    # path('auth/', ObtainAuthToken.as_view(), name='auth'),
    path('api/', include(router.urls,), name='api'),
    path('register/', UserCreateView.as_view(), name='register'),
]
