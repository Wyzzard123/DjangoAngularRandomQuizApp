import uuid

from django.contrib.auth.models import User
from django.db import models

from functools import reduce

from picklefield import PickledObjectField


class GenerateUUIDAbstract(models.Model):
    """
    Used to generate a unique UUID that does not serve as a primary key.
    """
    # Set the UUID when saving.
    uuid = models.UUIDField(blank=True, null=True, editable=False, verbose_name="UUID")

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = uuid.uuid4()
            # Check if uuid is unique and regenerate UUID
            # self.__class__ refers to the model class as you cannot access the "objects" manager directly through the
            #  instance of the descendant class. self.__class__ refers to, for example, "DashboardConfig" or
            #  "DashboardSnapshot".
            while self.__class__.objects.filter(uuid=self.uuid):
                self.uuid = uuid.uuid4()
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True


class TimeStampAbstract(models.Model):
    """
    Used to automatically update the time created and updated using Django's auto_now and auto_now_add.
    """
    created_at = models.DateTimeField('Date/Time Created', auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField('Date/Time Updated', auto_now=True, blank=True, null=True)

    # See https://docs.djangoproject.com/en/3.0/topics/db/models/#meta-inheritance
    class Meta:
        abstract = True


class UUIDAndTimeStampAbstract(GenerateUUIDAbstract, TimeStampAbstract):
    class Meta:
        abstract = True


class Topic(UUIDAndTimeStampAbstract):
    """
    A topic which can contain many questions. When creating a question, we will link it to a topic (or many topics).
    """
    creator = models.ForeignKey(User, verbose_name="Creator", related_name="topics", on_delete=models.CASCADE)
    name = models.CharField(max_length=256, verbose_name="Topic Name")

    def max_questions(self):
        """Return the max number of questions for a given topic and user."""
        return self.questions.count()

    def max_choices(self):
        """Returns the max number of choices for a given topic and user."""
        return reduce(lambda cumulative_total, answer_count_per_question: cumulative_total + answer_count_per_question,
               [question.answers.count() for question in self.questions.all()])

    def pool_of_choices(self):
        """Returns all choices for a given topic and user."""
        return Answer.objects.filter(creator=self.creator, questions__topic=self)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        default_related_name = "topics"
        unique_together = [["creator", "name"]]


class Answer(UUIDAndTimeStampAbstract):
    creator = models.ForeignKey(User, verbose_name="Creator", related_name="answers", on_delete=models.CASCADE)
    # If the answer is connected to the question, the answer is correct.
    text = models.TextField(verbose_name="Text")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        default_related_name = "answers"
        unique_together = [["creator", "text"]]


class Question(UUIDAndTimeStampAbstract):
    """
    A question with one correct answer.
    """
    creator = models.ForeignKey(User, verbose_name="Creator", related_name="questions", on_delete=models.CASCADE)
    topic = models.ManyToManyField(Topic, related_name="questions")
    answers = models.ManyToManyField(Answer, related_name="questions")
    text = models.TextField(verbose_name="Text")

    def has_one_answer(self):
        return self.answers.count() == 1

    @property
    def answer(self):
        """Returns the one right answer (model)"""
        if self.has_one_answer():
            return self.answers.all()[0]
        else:
            raise AttributeError("Question has multiple answers.")

    @property
    def answer_text(self):
        """Return the text of the one right answer."""
        if self.has_one_answer():
            return self.answers.all()[0].text
        else:
            raise AttributeError("Question has multiple answers.")

    @property
    def list_of_answer_text(self):
        """Return a list of text of valid answers"""
        return [answer.text for answer in self.answers.all()]

    def is_right_answer(self, answer_text):
        """Check if an answer is right"""
        if not Answer.objects.filter(creator=self.creator, text=answer_text):
            # If no such answer exists in the database, return False.
            return False
        if self.has_one_answer():
            # If the answer is the one correct answer, return True. Otherwise return False.
            return self.answer_text == answer_text
        else:
            # If there are multiple answers, check if the answer_text is in any of the correct answers.
            return answer_text in self.list_of_answer_text

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        default_related_name = "questions"
        unique_together = [["creator", "text"]]


class Quiz(UUIDAndTimeStampAbstract):
    """Holds a randomly generated quiz of a given ID or UUID for a particular user.
    This is used so we can check answers and also keep data about past quizzes.

    Quiz will be in this format:
     {
        "topic": topic_text,
        "questions": [
            {'question_text': question_text_1, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'},
            {'question_text': question_text_2, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'radio'},
            ...,
            {'question_text': question_text_n, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'}
        ]
    }
    """
    creator = models.ForeignKey(User, verbose_name="Creator", related_name="quizzes", on_delete=models.CASCADE)

    topic = models.ForeignKey(Topic, verbose_name=Topic, related_name="quizzes", on_delete=models.SET_NULL,
                              null=True, blank=True)

    # This will take in the quiz in generate_quiz.
    quiz = PickledObjectField(verbose_name="Quiz", editable=False)

    def get_quiz_with_uuid(self):
        """Passes a dict with the quiz and the UUID of this model."""
        return {'uuid': self.uuid, **self.quiz}

    def check_quiz_answers(self, chosen_answers):
        """TODO - See what the format of receiving the answers is.
        For each chosen answer per a given question, check if the answer is correct.

        Assuming that chosen_answers comes in the following format for now:
        [answer_text_1, [answer_text_2_1, answer_text_2_2], ...]

        Return a format similar to the quiz:

        {
        "topic": topic_text,
        "questions": [
            {'question_text': question_text_1, 'choices':
            [{'choice_text': choice_text_1, 'chosen': True, 'correct': True},
            {'choice_text': choice_text_2, 'chosen': False, 'correct': True},
             {'choice_text': choice_text_3, 'chosen': True, 'correct': False}, ... choice_text_n], 'question_type': 'checkbox',}
            ,
            ...,
        ],
        "no_of_correct_answers": 3,
        "no_of_wrong_answers": 2,
        "score": 0.6,
        }

        """
        questions = self.quiz['questions']
        no_of_correct_answers = 0
        no_of_wrong_answers = 0

        # For "questions": [{...}, {...}]... (See docstring)
        attempt_dict_questions_list = []
        for index, question, chosen_answer_set in enumerate(zip(questions, chosen_answers)):
            question_text = question['question_text']
            question_model = Question.objects.get(creator=self.creator, text=question_text)
            original_choice_list = question['choices']

            # To be passed as a dict into the attempt_dict_questions_list.
            updated_dict_question = {'question_text': question_text,
                                     'question_type': question['question_type'],
                                     'choices': []
                                     }
            for choice in original_choice_list:
                choice_text = choice
                chosen = choice_text in chosen_answer_set
                is_correct = question_model.is_right_answer(choice_text)
                updated_dict_question['choices'].append({
                    'choice_text': choice_text,
                    'chosen': chosen,
                    'correct': is_correct,
                })
                # If the correct answer was chosen, add to the score.
                if is_correct and chosen:
                    no_of_correct_answers += 1
                # Otherwise, if the correct answer was not chosen or if the answer was chosen and false, add to the
                #  no of wrong answers.
                else:
                    no_of_wrong_answers += 1
            attempt_dict_questions_list.append(updated_dict_question)

        score = no_of_correct_answers / (no_of_correct_answers + no_of_wrong_answers)

        quiz_attempt = {
            "topic": self.quiz["topic"],
            "questions": attempt_dict_questions_list,
            "no_of_correct_answers": no_of_correct_answers,
            "no_of_wrong_answers": no_of_wrong_answers,
            "score": score
        }

        QuizAttempt.objects.create(quiz=self, quiz_attempt=quiz_attempt, score=score)
        return quiz_attempt

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        default_related_name = "quizzes"


class QuizAttempt(UUIDAndTimeStampAbstract):
    """Saves the attempts at a quiz."""
    quiz = models.ForeignKey(Quiz, verbose_name="Quiz", on_delete=models.SET_NULL, related_name="quiz_attempts", blank=True,
                             null=True)
    quiz_attempt = PickledObjectField(verbose_name="Quiz Attempt", editable=False),
    score = models.FloatField(verbose_name="Score")

    class Meta:
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        default_related_name = "quiz_attempts"


