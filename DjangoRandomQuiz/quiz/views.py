from django.contrib.auth.models import User
from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework import viewsets

# from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope

from quiz.mixins import NoUpdateCreatorMixin
from quiz.models import Topic, Question, Answer
from quiz.serializers import TopicSerializer, QuestionSerializer, AnswerSerializer, UserSerializer


class TopicAPIView(NoUpdateCreatorMixin, viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL topics belonging to a user"""
    serializer_class = TopicSerializer

    permission_classes = (IsAuthenticated, TokenHasReadWriteScope)

    def get_queryset(self):
        user = self.request.user
        return Topic.objects.filter(creator=user)


class QuestionAPIView(NoUpdateCreatorMixin, viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL questions belonging to a user"""
    serializer_class = QuestionSerializer

    # authentication_classes = (TokenAuthentication, TokenHasReadWriteScope)
    permission_classes = (IsAuthenticated, TokenHasReadWriteScope)

    def get_queryset(self):
        user = self.request.user
        return Question.objects.filter(creator=user)


class AnswerAPIView(NoUpdateCreatorMixin, viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL answers belonging to a user"""
    serializer_class = AnswerSerializer

    # authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, TokenHasReadWriteScope)

    def get_queryset(self):
        user = self.request.user
        return Answer.objects.filter(creator=user)


class UserCreateView(generics.CreateAPIView):
    """Used to register users from the frontend.
    See: https://nemecek.be/blog/23/how-to-createregister-user-account-with-django-rest-framework-api"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Anyone should be able to register.
    permission_classes = (AllowAny, )
