from .models import Topic, Question, Answer
import random


def generate_list_of_wrong_choices(possible_wrong_choices, no_of_wrong_choices):
    """Returns a list of text of wrong_choice text."""
    possible_wrong_choices_copy = list(possible_wrong_choices)
    wrong_choices = []
    for _ in range(no_of_wrong_choices):
        wrong_choice = random.choice(possible_wrong_choices_copy)
        # Add wrong choices and retry if the wrong choice is already in the wrong_choices list.
        while wrong_choice in wrong_choices:
            wrong_choice = random.choice(possible_wrong_choices_copy)
        wrong_choices.append(wrong_choice)
        # Remove the wrong choice from the possible_wrong_choices_copy so that we don't end up in a possibly
        #  infinite loop.
        possible_wrong_choices_copy.remove(wrong_choice)
    # Return a list of the text of the wrong choices
    return [wrong_choice.text for wrong_choice in wrong_choices]


def generate_quiz(user_id, topic_id, no_of_questions, no_of_choices,
                  show_all_alternative_answers=False):
    """
    Generate a list of questions based on a topic text, number of questions per topic and number of choices per
    question.

    If no_of_questions is more than the number of Question models for a given User and Topic, the no_of_questions will
    be changed to the max number of Question models.

    If no_of_choices is more than the number of answer models for a given answer and topic, the no_of_choices will be
    changed to the max number of Answer models.

    The return value will take the following format:

    {
        "topic": topic_text,
        "questions": [
            {'question_text': question_text_1, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'},
            {'question_text': question_text_2, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'radio'},
            ...,
            {'question_text': question_text_n, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'question_type': 'checkbox'}
        ]
    }

    If show_all_alternative_answers is True (False by default), each question will (as far as possible within the
    no_of_choices constraint), each question will have all possible answers shown. Otherwise, the number of correct
    alternative answers shown will be random.

    For each question, if the max number of answers is more than one, the question will be a checkbox (multiple choices)
    instead of a radio button (one choice).
    """
    # Get quiz topic
    quiz_topic = Topic.objects.get(creator__id=user_id, name=topic_id)

    quiz = {"topic": quiz_topic.name,
            "questions": []}

    # Limit number of questions and number of choices
    max_questions = quiz_topic.max_questions()
    no_of_questions = no_of_questions if no_of_questions <= max_questions else max_questions

    max_choices = quiz_topic.max_choices()
    no_of_choices = no_of_choices if no_of_choices <= max_choices else max_choices

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
            no_of_wrong_choices = no_of_choices - 1

            possible_wrong_choices = quiz_choices.exclude(id=correct_answer.id)

            wrong_choices = generate_list_of_wrong_choices(possible_wrong_choices, no_of_wrong_choices)
            all_choices = [correct_answer.text, *wrong_choices]
        else:
            question_type = "checkbox"
            correct_answers = question.answers.all()

            possible_wrong_choices = quiz_choices
            # Chain .exclude() to exclude all correct answers from the set of wrong_choices.
            for correct_answer in correct_answers:
                possible_wrong_choices = possible_wrong_choices.exclude(id=correct_answer.id)

            # We have to calibrate the number of correct answers based on the max number of wrong choices. If we have
            #  too few possible wrong choices, we cannot have too few correct answers.
            max_no_of_wrong_choices = len(possible_wrong_choices)
            min_no_of_correct_answers = no_of_choices - max_no_of_wrong_choices

            # The number of correct answers cannot be higher than the number of choices, but it also cannot be higher
            #  than the total number of possible correct answers.
            max_no_of_correct_answers = min(correct_answers.count(), no_of_choices)

            # Randomly allocate the number of correct answers with a number between the minimum and maximum number of
            #  correct answers.
            if not show_all_alternative_answers:
                no_of_correct_answers = random.randint(min_no_of_correct_answers, max_no_of_correct_answers)
            else:
                # If we say show_all_alternative_answers, we will either show all the correct answers or the max no of
                #  choices per question, depending on which is lower.
                no_of_correct_answers = max_no_of_correct_answers

            # No of wrong choices will be no of choices minus no of correct answers.
            no_of_wrong_choices = no_of_choices - no_of_correct_answers

            wrong_choices = generate_list_of_wrong_choices(possible_wrong_choices, no_of_wrong_choices)
            correct_answers = random.sample([correct_answer.text for correct_answer in correct_answers], no_of_correct_answers)
            all_choices = [*correct_answers, *wrong_choices]
        # all_choices = [choice for choice in all_choices]
        # Shuffle the list of choices
        random.shuffle(all_choices)

        # Add the question dict to the quiz's questions field.
        quiz['questions'].append({
            'question_text': question_text,
            'choices': all_choices,
            'question_type': question_type
        })
    return quiz












            # TODO implement checkbox questions




