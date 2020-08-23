from .models import Topic, Question, Answer

def generate_quiz(user_id, topic_text, no_of_questions, no_of_choices,
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
            {'question': question_text_1, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'type': 'checkbox'},
            {'question': question_text_2, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'type': 'radio'},
            ...,
            {'question': question_text_n, 'choices': [choice_text_1, choice_text_2, ... choice_text_n], 'type': 'checkbox'}
        ]
    }

    If show_all_alternative_answers is True (False by default), each question will (as far as possible within the
    no_of_choices constraint), each question will have all possible answers shown. Otherwise, the number of correct
    alternative answers shown will be random.

    For each question, if the max number of answers is more than one, the question will be a checkbox (multiple choices)
    instead of a radio button (one choice).
    """
    quiz = {"topic": topic_text,
            "questions": []}

    quiz_topic = Topic.objects.get(creator__id=user_id, name=topic_text)

    max_questions = quiz_topic.max_questions()
    no_of_questions = no_of_questions if no_of_questions <= max_questions else max_questions

    max_choices = quiz_topic.max_choices()
    no_of_choices = no_of_choices if no_of_choices <= max_choices else max_choices

    all_questions = quiz_topic.questions.all()

    # TODO implement checkbox questions



