import random
import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from functools import reduce

from picklefield import PickledObjectField

from quiz.generate_quiz import generate_list_of_wrong_choices


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

    def generate_quiz(self, no_of_questions=4, no_of_choices=4,
                      show_all_alternative_answers=False,
                      fixed_choices_only=False
                      ):
        """
        Generate a list of questions based on a topic text, number of questions per topic and number of choices per
        question.

        If no_of_questions is more than the number of Question models for a given User and Topic, the no_of_questions will
        be changed to the max number of Question models.

        If no_of_choices is more than the number of answer models for a given answer and topic, the no_of_choices will be
        changed to the max number of Answer models.

        We will then save a dict with the following dict to the Quiz model (the id is added after saving once):

        {
            "topic": topic_id,
            "questions": [
                {'question_text': question_text_1, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'},
                {'question_text': question_text_2, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'radio'},
                ...,
                {'question_text': question_text_n, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'}
            ],
            "id": quiz_model_id,
        }

        If show_all_alternative_answers is True (False by default), each question will (as far as possible within the
        no_of_choices constraint), each question will have all possible answers shown. Otherwise, the number of correct
        alternative answers shown will be random.

        If fixed_choices_only is True (False by default), we will ignore no_of_choices and show_all_alternative_answers.
        Instead, we will show every possible correct and wrong answer for every given question (no_of_questions is still
        used). Essentially, this converts the app from a random quiz app to a normal fixed quiz app. Use this if you
        have enough wrong choices for all questions.

        For each question, if the max number of answers is more than one, the question will be a checkbox (multiple choices)
        instead of a radio button (one choice).
        """
        # TODO - Handle the case where the topic has no questions.

        # Get quiz topic
        quiz_topic = self

        quiz = {"topic": quiz_topic.id,
                "topic_name": quiz_topic.name,
                "questions": []}

        # Automatically set default values if invalid values are set (this should be caught in the frontend):
        no_of_questions = no_of_questions if no_of_questions > 0 else 4
        no_of_choices = no_of_choices if no_of_choices > 0 else 4

        # Limit number of questions and number of choices
        max_questions = quiz_topic.max_questions()
        no_of_questions = no_of_questions if no_of_questions <= max_questions else max_questions

        max_choices = quiz_topic.max_choices()
        no_of_choices = min(no_of_choices, max_choices)

        # Get the required number of questions in the right order.
        # Order by ('?') allows us to scramble the data randomly.
        quiz_questions = quiz_topic.questions.order_by('?')[:no_of_questions]

        # Get a queryset of choices available to the topic.
        quiz_choices = quiz_topic.pool_of_choices()

        for question in quiz_questions:
            question_text = question.text
            if question.has_one_answer():
                question_type = "radio"
                correct_answer = question.answer
                fixed_wrong_answers = question.wrong_answers.all()

                if fixed_choices_only:
                    no_of_wrong_choices = fixed_wrong_answers.count()
                    no_of_fixed_wrong_choices = no_of_wrong_choices
                else:
                    no_of_wrong_choices = no_of_choices - 1
                    no_of_fixed_wrong_choices = min(fixed_wrong_answers.count(), no_of_wrong_choices)

                # Set fixed wrong choices
                fixed_wrong_choices = generate_list_of_wrong_choices(fixed_wrong_answers, no_of_fixed_wrong_choices)

                if fixed_choices_only:
                    # No random wrong choices if using fixed_choices_only mode
                    random_wrong_choices = []
                else:
                    # Set random wrong answers
                    no_of_random_wrong_choices = max(0, no_of_wrong_choices - no_of_fixed_wrong_choices)
                    possible_random_wrong_choices = quiz_choices.exclude(id=correct_answer.id)

                    # Chain .exclude() to exclude all fixed wrong choices answers from the set of random_wrong_choices.
                    for fixed_wrong_answer in fixed_wrong_answers:
                        possible_random_wrong_choices = possible_random_wrong_choices.exclude(id=fixed_wrong_answer.id)

                    random_wrong_choices = generate_list_of_wrong_choices(possible_random_wrong_choices,
                                                                          no_of_random_wrong_choices)

                all_choices = [correct_answer.text, *fixed_wrong_choices, *random_wrong_choices]

            else:
                question_type = "checkbox"
                correct_answers = question.answers.all()
                if fixed_choices_only:
                    max_no_of_correct_answers = correct_answers.count()
                else:
                    # The number of correct answers cannot be higher than the number of choices, but it also cannot
                    # be higher than the total number of possible correct answers.
                    max_no_of_correct_answers = min(correct_answers.count(), no_of_choices)

                # Set fixed wrong answers
                fixed_wrong_answers = question.wrong_answers.all()
                no_of_fixed_wrong_answers = fixed_wrong_answers.count()

                if fixed_choices_only:
                    correct_choices = [correct_answer.text for correct_answer in correct_answers]
                    random_wrong_choices = []
                    no_of_fixed_wrong_choices = no_of_fixed_wrong_answers
                    fixed_wrong_choices = generate_list_of_wrong_choices(fixed_wrong_answers, no_of_fixed_wrong_choices)

                else:
                    possible_random_wrong_choices = quiz_choices
                    # Chain .exclude() to exclude all correct answers from the set of wrong_choices.
                    for correct_answer in correct_answers:
                        possible_random_wrong_choices = possible_random_wrong_choices.exclude(id=correct_answer.id)
                    # Chain .exclude() to exclude all fixed wrong choices answers from the set of random_wrong_choices.
                    for fixed_wrong_answer in fixed_wrong_answers:
                        possible_random_wrong_choices = possible_random_wrong_choices.exclude(id=fixed_wrong_answer.id)

                    # We have to calibrate the number of correct answers based on the max number of wrong choices. If
                    # we have too few possible wrong choices, we cannot have too few correct answers.
                    max_no_of_wrong_choices = len(possible_random_wrong_choices) + no_of_fixed_wrong_answers
                    # We will make sure to have at least one correct answer.
                    min_no_of_correct_answers = max(1, no_of_choices - max_no_of_wrong_choices)

                    # Randomly allocate the number of correct answers with a number between the minimum and maximum
                    # number of correct answers.
                    if not show_all_alternative_answers:
                        try:
                            no_of_correct_answers = random.randint(min_no_of_correct_answers, max_no_of_correct_answers)
                        except ValueError:
                            print(f"WARNING: Empty question: '{question_text}'")
                            continue
                    else:
                        # If we say show_all_alternative_answers, we will either show all the correct answers or the
                        # max no of choices per question, depending on which is lower.
                        no_of_correct_answers = max_no_of_correct_answers

                    # No of wrong choices will be no of choices minus no of correct answers.
                    no_of_wrong_choices = no_of_choices - no_of_correct_answers

                    no_of_fixed_wrong_choices = min(no_of_fixed_wrong_answers, no_of_wrong_choices)
                    fixed_wrong_choices = generate_list_of_wrong_choices(fixed_wrong_answers, no_of_fixed_wrong_choices)

                    no_of_random_wrong_choices = max(0, no_of_wrong_choices - no_of_fixed_wrong_choices)
                    random_wrong_choices = generate_list_of_wrong_choices(possible_random_wrong_choices,
                                                                          no_of_random_wrong_choices)
                    correct_choices = random.sample([correct_answer.text for correct_answer in correct_answers],
                                                    no_of_correct_answers)

                all_choices = [*correct_choices, *fixed_wrong_choices, *random_wrong_choices]
            # all_choices = [choice for choice in all_choices]
            # Shuffle the list of choices
            random.shuffle(all_choices)

            # Add the question dict to the quiz's questions field.
            quiz['questions'].append({
                'question_text': question_text,
                'choices': all_choices,
                'question_type': question_type
            })

        quiz_object = Quiz.objects.create(
            creator=self.creator,
            quiz=quiz,
        )
        quiz_object.quiz.update({'id': quiz_object.id})
        quiz_object.save()
        return quiz_object


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
    wrong_answers = models.ManyToManyField(Answer, related_name="wrong_questions", blank=True)
    text = models.TextField(verbose_name="Text")

    def clean(self, *args, **kwargs):
        # If there are correct answers in the wrong_answers, raise an error
        # TODO - This validation currently does not work properly in the admin page.
        if self.answers.all() & self.wrong_answers.all():
            raise ValidationError({"wrong_answers": "Wrong answers should not be contained in the correct answers"})
        return super().clean()

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
    """
    Holds a randomly generated quiz of a given ID or UUID for a particular user.
    This is used so we can check answers and also keep data about past quizzes.

    Quiz will be in this format:
     {
        "topic": topic_text,
        "questions": [
            {'question_text': question_text_1, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'},
            {'question_text': question_text_2, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'radio'},
            ...,
            {'question_text': question_text_n, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'}
        ],
        "id": quiz_model_id,
    }
    The id field allows us to get the same quiz back when we check answers.
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

        Assuming that chosen_answers comes in the following format with a list of lists of choices:
        [[answer_text_1], [answer_text_2_1, answer_text_2_2], ...]

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
        "id": <quiz_attempt_id>
        }

        """
        questions = self.quiz['questions']
        no_of_correct_answers = 0
        no_of_wrong_answers = 0

        # The total possible score will be the total of all the number of correct answers.
        possible_points = 0

        # The total score for the quiz.
        # Answering a radio question correctly gives 1 / 1 points. Answering wrongly gives 0 points.
        # Choosing a wrong checkbox question answer will subtract 1 from the points that were scored for that question
        #  with a minimum of 0 points.
        total_points_scored = 0

        # For "questions": [{...}, {...}]... (See docstring)
        attempt_dict_questions_list = []
        for question, chosen_answer_set in zip(questions, chosen_answers):
            question_text = question['question_text']
            question_type = question['question_type']
            question_model = Question.objects.get(creator=self.creator, text=question_text)
            original_choice_list = question['choices']

            # To be passed as a dict into the attempt_dict_questions_list.
            updated_dict_question = {'question_text': question_text,
                                     'question_type': question_type,
                                     'choices': [],
                                     }

            # Start the score counter at 0.

            # The total question points without deduction
            question_points = 0

            # The total penalty.
            penalty = 0

            # The score will be the question_points - penalty with a minimum of 0.
            question_points_scored = 0
            possible_question_points = 0
            for choice in original_choice_list:
                choice_text = choice
                chosen = choice_text in chosen_answer_set
                is_correct = question_model.is_right_answer(choice_text)
                updated_dict_question['choices'].append({
                    'choice_text': choice_text,
                    'chosen': chosen,
                    'correct': is_correct,
                    # We will also add the number of points scored per question and the possible number of points per
                    #  question
                })
                if is_correct:
                    # The possible score will increase per answer that is correct (though not necessarily chosen).
                    possible_question_points += 1

                if is_correct and chosen:
                    # If the correct answer was chosen, add to the score.
                    no_of_correct_answers += 1
                    question_points += 1
                elif is_correct and not chosen:
                    # Otherwise, if the correct answer was not chosen, add to the no of wrong (unchosen) answers.
                    no_of_wrong_answers += 1
                elif not is_correct and chosen:
                    # However, if the wrong answer is chosen, penalize for choosing the wrong answer for checkbox type
                    #  questions to disincentivize clicking all the checkboxes.
                    if question_type == 'checkbox':
                        penalty += 1
            # Reset question score to 0 if it falls below 0.
            question_points_scored = question_points - penalty if (question_points - penalty) >= 0 else 0
            # Add the possible question score to the possible quiz score.
            possible_points += possible_question_points
            # Add the question score to the total score
            total_points_scored += question_points_scored
            updated_dict_question.update({
                'question_points_scored': question_points_scored,
                'possible_question_points': possible_question_points,
                'question_points_before_penalty': question_points,
                'penalty': penalty
            })
            attempt_dict_questions_list.append(updated_dict_question)

        # The final score (which can be multiplied by 100% for percentage) is the total score divided by the possible
        #  quiz score.
        score = total_points_scored / possible_points

        quiz_attempt = {
            "topic_id": self.quiz["topic"],
            "topic_name": self.quiz["topic_name"],
            "questions": attempt_dict_questions_list,
            "no_of_correct_answers": no_of_correct_answers,
            "no_of_wrong_answers": no_of_wrong_answers,
            "score": score,
            "total_points_scored": total_points_scored,
            "possible_points": possible_points
        }

        quiz_attempt_object = QuizAttempt.objects.create(quiz=self, quiz_attempt=quiz_attempt, score=score)
        # Add in the quiz_attempt id to the quiz_attempt dictionary.
        quiz_attempt_object.quiz_attempt['id'] = quiz_attempt_object.id
        quiz_attempt_object.save()
        return quiz_attempt_object

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        default_related_name = "quizzes"


class QuizAttempt(UUIDAndTimeStampAbstract):
    """Saves the attempts at a quiz."""
    quiz = models.ForeignKey(Quiz, verbose_name="Quiz", on_delete=models.SET_NULL, related_name="quiz_attempts", blank=True,
                             null=True)
    quiz_attempt = PickledObjectField(verbose_name="Quiz Attempt", editable=False)
    score = models.FloatField(verbose_name="Score")

    class Meta:
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        default_related_name = "quiz_attempts"


