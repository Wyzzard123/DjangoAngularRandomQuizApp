from django.contrib.auth.models import User

# Create your views here.
from rest_framework import generics, status
from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated, AllowAny

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework.response import Response

from quiz.mixins import NoUpdateCreatorMixin
from quiz.models import Topic, Question, Answer, Quiz
from quiz.serializers import TopicSerializer, QuestionSerializer, AnswerSerializer, UserSerializer, \
    QuestionAnswerSerializer, QuizSerializer, QuizAnswerSerializer


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

        curl -X POST -H "Authorization: Bearer <Token>" -H "Content-Type: application/json"
          --data '{"topic":"<topic_id>","question":"<question_id>","answers":["<answer_text_1>","<answer_text_2>",
          "<answer_text_3>"]}' "127.0.0.1:8000/api/create_qa/"
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


class GenerateQuizAPIView(QuizViewSet):
    """
    For this end point, we must pass in a topic ID. We will then get the relevant topic and generate a quiz using
    no_of_choices and no_of_questions
    """
    def update(self, request, pk, format=None):
        """
        Pass in the pk of a topic as the 'pk'. We will use this topic and return a random quiz.

        curl -X PUT -H "Authorization: Bearer <Token>" -H "Content-Type: application/json"
         --data '{"no_of_questions":"<no_of_questions>","no_of_choices":"<no_of_choices>"}'
         "127.0.0.1:8000/api/generate_quiz/<topic_id>/"
         """
        try:
            # Get the relevant topic.
            topic = self.topic_queryset().get(id=pk)
        except Exception as e:
            # Topic does not exist.
            return Response({"Error": "Topic Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = QuizSerializer(data=request.data)

        if serializer.is_valid():
            no_of_questions = serializer.validated_data['no_of_questions']
            no_of_choices = serializer.validated_data['no_of_choices']
            randomly_generated_quiz = topic.generate_quiz(no_of_questions=no_of_questions, no_of_choices=no_of_choices).quiz
            return Response(randomly_generated_quiz, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckQuizAnswersAPIView(viewsets.ViewSet):
    """
    Takes in a list of answers and attempts to answer a quiz of a particular ID (passed in as the pk).

    Returns a dict with the quiz answers.

    curl -X GET -H "Authorization: Bearer <Token>" -H "Content-Type: application/json"
         --data '{"answers":[[answer_text_1], [answer_text_2_1, answer_text_2_2], ...]}'
         "<url>/api/attempt_quiz/<quiz_id>/"
    """
    def quiz_queryset(self):
        """Only search topics from what the user has created."""
        return Quiz.objects.filter(creator=self.request.user)

    def retrieve(self, request, pk):
        """
        Pass in the pk of a quiz as the 'pk'. We will attempt this particular quiz and return the attempt dictionary.

        curl -X GET -H "Authorization: Bearer <Token>" -H "Content-Type: application/json"
         --data '{"answers":[[answer_text_1], [answer_text_2_1, answer_text_2_2], ...]}'
         "<url>/api/attempt_quiz/<quiz_id>/"
             """
        try:
            # Get the relevant topic.
            quiz = self.quiz_queryset().get(id=pk)
        except Exception as e:
            # Topic does not exist.
            return Response({"Error": "Quiz Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = QuizAnswerSerializer(data=request.data)
        if serializer.is_valid():
            chosen_answers = serializer.validated_data['answers']
            quiz_attempt = quiz.check_quiz_answers(chosen_answers=chosen_answers).quiz_attempt
            return Response(quiz_attempt, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class UserCreateView(generics.CreateAPIView):
    """Used to register users from the frontend.
    See: https://nemecek.be/blog/23/how-to-createregister-user-account-with-django-rest-framework-api"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # Anyone should be able to register.
    permission_classes = (AllowAny, )
