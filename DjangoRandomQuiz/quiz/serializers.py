from rest_framework import serializers

from .models import Topic, Question, Answer


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        # You must reference the creator as this is not null. Otherwise, we cannot create the serializer.
        fields = ['id', 'creator', 'name']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'topic', 'creator', 'text', 'answers']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'creator', 'text', 'questions']
