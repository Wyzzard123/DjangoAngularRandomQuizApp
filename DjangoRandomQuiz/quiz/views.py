from django.contrib.auth.models import User

# Create your views here.
from rest_framework import generics, status
from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated, AllowAny

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework.response import Response

from quiz.mixins import NoUpdateCreatorMixin
from quiz.models import Topic, Question, Answer
from quiz.serializers import TopicSerializer, QuestionSerializer, AnswerSerializer, UserSerializer, \
    QuestionAnswerSerializer


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

    permission_classes = (IsAuthenticated, TokenHasReadWriteScope)

    def get_queryset(self):
        user = self.request.user
        return Answer.objects.filter(creator=user)


class QuizViewSet(viewsets.ViewSet):
    """
    Defines a queryset for the topic, answer and question models restricted to the current user. The
    generate quiz method will use this.
    """
    def topic_queryset(self):
        """Only search topics from what the user has created."""
        return Topic.objects.filter(creator=self.request.user)

    def answer_queryset(self):
        """Only search answers from what the user has created."""
        return Answer.objects.filter(creator=self.request.user)

    def question_queryset(self):
        """Only search questions from what the user has created."""
        return Question.objects.filter(creator=self.request.user)


class QuestionAnswerCreateAPIView(QuizViewSet):
    """
    Create a question with one or more answers.

    See https://www.django-rest-framework.org/tutorial/3-class-based-views/ for how to create an API View.
    """
    # Using 'create' instead of post so we can use a ViewSet and register to the router.
    # See https://stackoverflow.com/questions/30389248/how-can-i-register-a-single-view-not-a-viewset-on-my-router
    def create(self, request, format=None):
        """
        Given a topic ID, question text and list of text for answers, create a question, add the topic and add the
        answers. If the questions, topics and answers already exist in the database for the user, just update the
        existing ones.
        """
        serializer = QuestionAnswerSerializer(data=request.data)
        if serializer.is_valid():
            topic_id = serializer.validated_data['topic']
            question_text = serializer.validated_data['question']
            list_of_answer_text = serializer.validated_data['answers']
            try:
                # Get the relevant topic.
                topic = self.topic_queryset().get(id=topic_id)
            except Exception as e:
                # Topic does not exist.
                return Response({"Error": "Topic Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

            user = self.request.user
            list_of_answer_instances = []
            for answer_text in list_of_answer_text:
                if self.answer_queryset().filter(text=answer_text):
                    # If the answer already exists, for this user, we will use this answer.
                    list_of_answer_instances.append(self.answer_queryset().get(text=answer_text))
                else:
                    # Otherwise, we create a new answer object.
                    new_answer = Answer.objects.create(text=answer_text, creator=user)
                    list_of_answer_text.append(new_answer)

            # If the question already exists in the database, we will just add the topic and the answers to this question
            if self.question_queryset().filter(text=question_text):
                question = Question.objects.get(text=question_text)
                question.topic.add(topic)
                question.answers.add(*list_of_answer_instances)
            else:
                # Otherwise, create a new question then add to the database.
                question = Question.objects.create(text=question_text, creator=user)
                question.topic.add(topic)
                question.answers.add(*list_of_answer_instances)
            # Save the question to the database.
            question.save()
            response_dict = {
                'topic': topic.id,
                'question': question.id,
                'answers': [answer.id for answer in list_of_answer_instances]
            }
            return Response(response_dict, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCreateView(generics.CreateAPIView):
    """Used to register users from the frontend.
    See: https://nemecek.be/blog/23/how-to-createregister-user-account-with-django-rest-framework-api"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Anyone should be able to register.
    permission_classes = (AllowAny, )
