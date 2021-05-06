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

    def topic_queryset(self):
        user = self.request.user
        return Topic.objects.filter(creator=user)

    def update(self, request, *args, **kwargs):
        """
        When we update, we only want to be able to edit the text. However, the standard model serializer gives us
        problems if we do not pass in a creator, topic, and list of answers.

        We cannot avoid passing in a topic as the topic is a many to many field and there may be many topics for one
        question. However, we can pass in the existing list of answers.

        Hence, we will simply add them here.

        If we update, first check whether the question is connected to more than one topic.

        If so, we will need to remove the old question model from the question, and create a new answer model (or use
        another existing model with the same text) then connect it to the intended question.


        TODO - Refactor this
        """
        question = self.get_object()

        topic = None

        if request.data.get('topic'):
            topic_id = request.data.pop('topic')
            try:
                # Get the relevant topic.
                topic = self.topic_queryset().get(id=topic_id)
            except Exception as e:
                # Topic does not exist.
                return Response({"error_description": "Topic Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)

        request.data.update({
            'topic': [topic.id for topic in question.topic.all()],
            'answers': [answer.id for answer in question.answers.all()],

            # TODO - This should be in a mixin, but right now it doesnt work.
            'creator': self.request.user.id
        })
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(question, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # The new answer text.
        updated_question_text = serializer.validated_data['text']

        if question.topic.count() <= 1:
            # If the answer being updated has only one question (or none), then simply perform update as per the normal API
            #  update view.
            self.perform_update(serializer)
            if getattr(question, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                question._prefetched_objects_cache = {}

            response_dict = {
                'id': question.id,
                'creator': question.creator.id,
                'text': serializer.validated_data['text'],
                'topic': [topic.id for topic in question.topic.all()],
                'answers': [answer.id for answer in question.answers.all()]
            }

            return Response(response_dict, status=status.HTTP_200_OK)
        else:
            if not topic:
                return Response({"error_description": "As there are multiple topics with this question, "
                                                      "you must pass a topic id (with 'topic')"
                                                      "in the request for the answer you wish to edit."},
                                status=status.HTTP_400_BAD_REQUEST)
            # Otherwise, create a new model separate from the existing one and attach that to the model instead.
            # Remove the current answer from the model.
            question.topic.remove(topic)

            if self.get_queryset().filter(text=updated_question_text):
                # If the updated question text matches another question already in the database, add that to the
                # existing question.
                new_question = self.get_queryset().get(text=updated_question_text)
                topic.questions.add(new_question)
            else:
                # Otherwise, create a new answer object and add that to the question.
                new_question = Question.objects.create(text=updated_question_text,
                                                       creator=self.request.user)
                topic.questions.add(new_question)
            response_dict = {
                'id': new_question.id,
                'creator': new_question.creator.id,
                'text': new_question.text,
                'topic': [topic.id for topic in question.topic.all()],
                'answers': [answer.id for answer in question.answers.all()]
            }
            # Return the new updated answer as a dict.
            return Response(response_dict, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Only destroy the question for the given topic as there may be multiples of the same question.
        We must pass in the question ID.
        """
        question = self.get_object()
        topic = None

        # If we have passed in question_id, we will take that out of the request data to avoid issues with
        #  the serializer.
        if request.data.get('topic_id'):
            topic_id = request.data.pop('topic_id')
            try:
                # Get the relevant topic.
                topic = self.topic_queryset().get(id=topic_id)
            except Exception as e:
                # Topic does not exist.
                return Response({"error_description": "Topic Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        if question.topic.count() == 0:
            # If there is no topic attached, just delete the question.
            self.perform_destroy(question)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            if not topic:
                return Response({"error_description": "As there are multiple topics with this question, "
                                                      "you must pass a question_id in the request for the question you "
                                                      "wish to edit."},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # If we have multiple topics, remove the topic from the list of topic for this particular
                #  question.
                question.topic.remove(topic)
                return Response(status=status.HTTP_204_NO_CONTENT)


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
        answer = self.get_object()
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

        # Check if the answer is meant to be correct
        correct = None
        if request.data.get('correct') is not None:
            correct = request.data.pop('correct')

        request.data.update({
            'questions': [question.id for question in answer.questions.all()],
            # TODO - This should be in a mixin, but right now it doesnt work.
            'creator': self.request.user.id
        })

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(answer, data=request.data, partial=partial)
        # serializer.is_valid(raise_exception=True)

        # The new answer text. Use strip() as is_valid() will do this as well.
        updated_answer_text = request.data['text'].strip()

        if answer.questions.count() + answer.wrong_questions.count() <= 1:
            # TODO - Check for whether we have an old answer.

            if answer.questions.count() + answer.wrong_questions.count() == 0 and question is None:
                return Response({"error_description": "This is a new answer. You must pass in a question_id"},
                                status=status.HTTP_400_BAD_REQUEST)
            elif answer.questions.count() + answer.wrong_questions.count() == 1 and question is None:
                if answer.questions.all():
                    question = answer.questions.get()
                else:
                    question = answer.wrong_questions.get()

            # If the answer being updated has only one question (or none), then simply perform update as per the normal API
            #  update view if there is no question with the same updated answer text.
            if not self.get_queryset().filter(text=updated_answer_text):
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                if getattr(answer, '_prefetched_objects_cache', None):
                    # If 'prefetch_related' has been applied to a queryset, we need to
                    # forcibly invalidate the prefetch cache on the instance.
                    answer._prefetched_objects_cache = {}
            else:
                # If there is an old answer with the same text, we will delete the current answer (since there is 0 or
                # one question that reference(s) it) then reference the old answer instead:

                # Try to get the old answer first. If we get an error, then we will not delete the previously referenced
                #  answer.
                new_answer = self.get_queryset().filter(text=updated_answer_text).get()

                # Delete the old answer and reference the new one.
                answer.delete()
                answer = new_answer

            # If the answer has been changed to wrong or right, switch the answer around.
            if correct is True and question.wrong_answers.filter(id=answer.id):
                question.wrong_answers.remove(answer)
                question.answers.add(answer)

            if correct is False and question.answers.filter(id=answer.id):
                question.answers.remove(answer)
                question.wrong_answers.add(answer)

            response_dict = {
                'id': answer.id,
                'creator': answer.creator.id,
                'text': updated_answer_text,
                'questions': [question.id for question in answer.questions.all()],
                'correct': correct
            }

            return Response(response_dict, status.HTTP_200_OK)
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

            else:
                # TODO - Correct is being returned as null
                # Otherwise, create a new answer object and add that to the question.
                new_answer = Answer.objects.create(text=updated_answer_text,
                                                   creator=self.request.user)

            # Add to correct or wrong answers
            if correct is True or correct is None:
                question.answers.add(new_answer)
            else:
                # Check that the answer isn't already in the correct answers of the question. Ifit is, remove it.
                if new_answer in question.answers.all():
                    question.answers.remove(new_answer)

                question.wrong_answers.add(new_answer)

            response_dict = {
                'id': new_answer.id,
                'creator': new_answer.creator.id,
                'text': updated_answer_text,
                'questions': [question.id for question in new_answer.questions.all()],
                'correct': correct
            }
            # Return the new updated answer as a dict.
            return Response(response_dict, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Only destroy the object for the given question as there may be multiples of the same answer.
        We must pass in the question ID.
        """
        answer = self.get_object()
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
        if answer.questions.count() == 0:
            # If there is no question attached, just delete the answer.
            self.perform_destroy(answer)
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif answer.questions.count() == 1:
            question = answer.questions.get()

            # Check if the question has more than one answer. If it only has one answer left, do not delete.
            if question.answers.count() > 1:
                self.perform_destroy(answer)
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error_description": "This question has only one answer left. Add another answer "
                                                      "before deleting the question."},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            if not question:
                return Response({"error_description": "As there are multiple questions with this answer, "
                                                      "you must pass a question_id in the request for the answer you "
                                                      "wish to edit."},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # Check if the question has more than one answer. If it only has one answer left, do not delete.
                if question.answers.count() > 1:
                    self.perform_destroy(answer)
                    return Response(status=status.HTTP_204_NO_CONTENT)

                # If we have multiple questions, remove the question from the list of questions for this particular
                #  answer.
                answer.questions.remove(question)
                return Response(status=status.HTTP_204_NO_CONTENT)


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
                'answers': [],
                'wrong_answers': []
            }
            for answer in question.answers.all():
                answer_dict = {
                    'answer_id': answer.id,
                    'answer_text': answer.text,
                }
                question_dict['answers'].append(answer_dict)

            for wrong_answer in question.wrong_answers.all():
                wrong_answer_dict = {
                    'answer_id': wrong_answer.id,
                    'answer_text': wrong_answer.text
                }
                question_dict['wrong_answers'].append(wrong_answer_dict)
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
            list_of_wrong_answer_text = serializer.validated_data.get('wrong_answers') or []

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
                    list_of_answer_instances.append(new_answer)

            # Get wrong answers
            list_of_wrong_answer_instances = []
            for answer_text in list_of_wrong_answer_text:
                if self.answer_queryset().filter(text=answer_text):
                    # If the answer already exists, for this user, we will use this answer.
                    list_of_wrong_answer_instances.append(self.answer_queryset().get(text=answer_text))
                else:
                    # Otherwise, we create a new answer object.
                    new_answer = Answer.objects.create(text=answer_text, creator=user)
                    list_of_wrong_answer_instances.append(new_answer)

            # If the question already exists in the database, we will just add the topic and the answers to this question
            if self.question_queryset().filter(text=question_text):
                question = Question.objects.get(text=question_text)
                question.topic.add(topic)
                question.answers.add(*list_of_answer_instances)
                question.wrong_answers.add(*list_of_wrong_answer_instances)
            else:
                # Otherwise, create a new question then add to the database.
                question = Question.objects.create(text=question_text, creator=user)
                question.topic.add(topic)
                question.answers.add(*list_of_answer_instances)
                question.wrong_answers.add(*list_of_wrong_answer_instances)

            # Save the question to the database.
            question.save()

            response_dict = {
                'topic': topic.id,
                'question_id': question.id,
                'question_text': question.text,
                'answers': [],
                'wrong_answers': [],
            }

            for answer in question.answers.all():
                answer_dict = {
                    'answer_id': answer.id,
                    'answer_text': answer.text,
                }
                response_dict['answers'].append(answer_dict)

            for answer in question.wrong_answers.all():
                wrong_answer_dict = {
                    'answer_id': answer.id,
                    'answer_text': answer.text,
                }
                response_dict['wrong_answers'].append(wrong_answer_dict)

            return Response(response_dict, status=status.HTTP_201_CREATED)

        # Compile all errors into an error_description
        error_description_list = []
        for key, _ in serializer.errors.items():
            if key == 'question':
                error_description_list.append("Question cannot be blank.")
            if key == 'answers':
                error_description_list.append("Answers cannot be blank.")

        error_description = " ".join(error_description_list)

        return Response({"error_description": error_description}, status=status.HTTP_400_BAD_REQUEST)


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
    permission_classes = (AllowAny,)
