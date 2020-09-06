from django.contrib.auth.models import User

# Create your views here.
from rest_framework import generics, status
from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated, AllowAny

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework.response import Response

from quiz.mixins import NoUpdateCreatorMixin, UserDataBasedOnRequestMixin
from quiz.models import Topic, Question, Answer, Quiz
from quiz.serializers import TopicSerializer, QuestionSerializer, AnswerSerializer, UserSerializer, \
    QuestionAnswerSerializer, QuizSerializer, QuizAnswerSerializer


class TopicAPIView(UserDataBasedOnRequestMixin, NoUpdateCreatorMixin, viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL topics belonging to a user"""
    serializer_class = TopicSerializer

    permission_classes = (IsAuthenticated, TokenHasReadWriteScope)

    def get_queryset(self):
        user = self.request.user
        return Topic.objects.filter(creator=user)


class QuestionAPIView(UserDataBasedOnRequestMixin, NoUpdateCreatorMixin, viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL questions belonging to a user"""
    serializer_class = QuestionSerializer

    # authentication_classes = (TokenAuthentication, TokenHasReadWriteScope)
    permission_classes = (IsAuthenticated, TokenHasReadWriteScope)

    def get_queryset(self):
        user = self.request.user
        return Question.objects.filter(creator=user)


class AnswerAPIView(UserDataBasedOnRequestMixin, NoUpdateCreatorMixin, viewsets.ModelViewSet):
    """View to create, read, update and destroy ALL answers belonging to a user"""
    serializer_class = AnswerSerializer

    permission_classes = (IsAuthenticated, TokenHasReadWriteScope)

    def get_queryset(self):
        user = self.request.user
        return Answer.objects.filter(creator=user)

    def question_queryset(self):
        """Only search questions from what the user has created."""
        return Question.objects.filter(creator=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        If we update, first check whether the answer is connected to more than one question.

        If so, we will need to remove the old answer model from the question, and create a new answer model (or use
        another existing model with the same text) then connect it to the intended question.

        To ensure this is achieved, we must allow an optional parameter for a question_id to be passed in
        along with the answer itself, so that we can create the appropriate new model.
        """
        question = None

        # If we have passed in question_id, we will take that out of the request data to avoid issues with
        #  the serializer.
        if request.data.get('question_id'):
            question_id = request.data.pop('question_id')
            try:
                # Get the relevant topic.
                question = self.question_queryset().get(id=question_id)
            except Exception as e:
                # Topic does not exist.
                return Response({"error_description": "Question Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

        partial = kwargs.pop('partial', False)
        answer = self.get_object()
        serializer = self.get_serializer(answer, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # The new answer text.
        updated_answer_text = serializer.validated_data['text']

        if answer.questions.count() <= 1:
            # If the answer being updated has only one question (or none), then simply perform update as per the normal API
            #  update view.
            self.perform_update(serializer)
            if getattr(answer, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                answer._prefetched_objects_cache = {}
            return Response(serializer.data)
        else:
            if not question:
                return Response({"error_description": "As there are multiple questions with this answer, "
                                                      "you must pass a question_id in the request for the answer you "
                                                      "wish to edit."},
                                status=status.HTTP_400_BAD_REQUEST)
            # Otherwise, create a new model separate from the existing one and attach that to the model instead.
            # Remove the current answer from the model.
            question.answers.remove(answer)

            if self.get_queryset().filter(text=updated_answer_text):
                # If the updated answer text matches another answer already in the database, add that to the existing
                #  question.
                new_answer = self.get_queryset().get(text=updated_answer_text)
                question.answers.add(new_answer)
            else:
                # Otherwise, create a new answer object and add that to the question.
                new_answer = Answer.objects.create(text=updated_answer_text,
                                                   creator=self.request.user)
                question.answers.add(new_answer)
            response_dict = {
                'id': new_answer.id,
                'creator': new_answer.creator.id,
                'text': new_answer.text,
                'questions': [question.id for question in new_answer.questions.all()]
            }
            # Return the new updated answer as a dict.
            return Response(response_dict, status=status.HTTP_200_OK)


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

    def quiz_queryset(self):
        """Only search questions from what the user has created."""
        return Quiz.objects.filter(creator=self.request.user)


class QuestionAnswerAPIView(QuizViewSet):
    """
    This serves as the primary endpoint to retrieve a list of questions and answers for a given topic, and to then
    edit said questions and answers.

    The retrieve view takes in a topic ID as the PK then gets all the available questions for that topic with their
    answers. These questions can then each be edited and sent to the update view.

    The create view creates a question with one or more answers.

    See https://www.django-rest-framework.org/tutorial/3-class-based-views/ for how to create an API View.
    """

    def retrieve(self, request, pk, format=None):
        """
        Given a topic ID, get a list of questions, and a list of answers for each question.

        Return a dict with the topic_id, and a list of questions with answers.

        {
            # We will not allow people to change the topic name through here.
            'topic':        topic.id,
            'qna':        [{'question_id': question1.id, 'question_text': question1.text,
                           'answers': [{'answer_id': 'answer1.id', 'answer_text': answer1.text},
                                       {'answer_id': 'answer2.id', 'answer_text': answer2.text}]},
                            {'question_id': question2.id, 'question_text': question2.text,
                           'answers': [{'answer_id': 'answer1.id', 'answer_text': answer1.text},
                                       {'answer_id': 'answer2.id', 'answer_text': answer2.text}]}]

        }
        """
        topic_id = pk

        try:
            # Get the relevant topic.
            topic = self.topic_queryset().get(id=topic_id)
        except Exception as e:
            # Topic does not exist.
            return Response({"error_description": "Topic Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

        response_dict = {
            'topic': topic.id,
            'qna': []
        }

        for question in topic.questions.all():
            question_dict = {
                'question_id': question.id,
                'question_text': question.text,
                'answers': []
            }
            for answer in question.answers.all():
                answer_dict = {
                    'answer_id': answer.id,
                    'answer_text': answer.text,
                }
                question_dict['answers'].append(answer_dict)
            response_dict['qna'].append(question_dict)

        return Response(response_dict, status=status.HTTP_200_OK)

    # Using 'create' instead of post so we can use a ViewSet and register to the router.
    # See https://stackoverflow.com/questions/30389248/how-can-i-register-a-single-view-not-a-viewset-on-my-router
    def create(self, request, format=None):
        """
        Given a topic ID, question text and list of text for answers, create a question, add the topic and add the
        answers. If the questions, topics and answers already exist in the database for the user, just update the
        existing ones.

        curl -X POST -H "Authorization: Bearer <Token>" -H "Content-Type: application/json"
          --data '{"topic":"<topic_id>","question":"<question_id>","answers":["<answer_text_1>","<answer_text_2>",
          "<answer_text_3>"]}' "127.0.0.1:8000/api/qna/"
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
                return Response({"error_description": "Topic Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

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

    def retrieve(self, request, pk, format=None):
        """
        Pass in the pk of a quiz, and we will return an older quiz. This will be used to retry quizzes.
        """
        try:
            # Get the relevant topic.
            quiz = self.quiz_queryset().get(id=pk).quiz
        except Exception as e:
            # Topic does not exist.
            return Response({"error_description": "Quiz Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(quiz, status=status.HTTP_200_OK)

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
            return Response({"error_description": "Topic does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        if not topic.questions.all():
            return Response({"error_description": "Topic has no questions. Add some questions to the topic first."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = QuizSerializer(data=request.data)

        if serializer.is_valid():
            no_of_questions = serializer.validated_data['no_of_questions']
            no_of_choices = serializer.validated_data['no_of_choices']
            randomly_generated_quiz = topic.generate_quiz(no_of_questions=no_of_questions,
                                                          no_of_choices=no_of_choices).quiz
            return Response(randomly_generated_quiz, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckQuizAnswersAPIView(QuizViewSet):
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

    def update(self, request, pk):
        """
        Check quiz answers.

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
            return Response({"error_description": "Quiz Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = QuizAnswerSerializer(data=request.data)
        if serializer.is_valid():
            chosen_answers = serializer.validated_data['answers']
            # TODO - Add validation
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
