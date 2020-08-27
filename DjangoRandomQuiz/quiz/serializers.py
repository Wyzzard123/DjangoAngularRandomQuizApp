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


class QuestionAnswerSerializer(serializers.Serializer):
    """Create a question with a set of given answers using this serializer."""
    # Topic field takes an ID.
    topic = serializers.IntegerField()
    question = serializers.CharField(max_length=None)

    # We will have a list of answers so we can have as many answers connected to one question as we want.
    answers = serializers.ListField(
        child=serializers.CharField(max_length=None)
    )


class QuizSerializer(serializers.Serializer):
    """Pass in fields to generate a quiz for a given topic with a no_of_choices and no_of_questions."""
    # Topic ID
    topic = serializers.IntegerField()

    # Parameters to be passed in to the generate_quiz method of topic.
    no_of_questions = serializers.IntegerField()
    no_of_choices = serializers.IntegerField()
    show_all_alternative_answers = serializers.BooleanField(default=False)

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
