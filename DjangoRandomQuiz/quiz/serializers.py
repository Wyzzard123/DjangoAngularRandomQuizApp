from django.contrib.auth.models import User
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


class UserSerializer(serializers.ModelSerializer):
    """
    Used to register users.
    See https://nemecek.be/blog/23/how-to-createregister-user-account-with-django-rest-framework-api
    """
    class Meta:
        model = User
        fields = ['username', 'password']
        # Make the password writeonly so that we do not see the password in the response
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Get the password and remove it from the validated_data
        password = validated_data.pop('password')

        # Create the user with just the username
        user = User(**validated_data)

        # Set the password separately
        user.set_password(password)

        # Save to the database
        user.save()

        return user
