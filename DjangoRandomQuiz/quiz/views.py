from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework import viewsets

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from quiz.models import Topic, Question, Answer
from quiz.serializers import TopicSerializer, QuestionSerializer, AnswerSerializer


class TopicAPIView(viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL topics belonging to a user"""
    serializer_class = TopicSerializer

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Topic.objects.filter(creator=user)


class QuestionAPIView(viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL questions belonging to a user"""
    serializer_class = QuestionSerializer

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Question.objects.filter(creator=user)


class AnswerAPIView(viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL answers belonging to a user"""
    serializer_class = AnswerSerializer

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return Answer.objects.filter(creator=user)
