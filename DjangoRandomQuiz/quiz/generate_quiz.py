import random


def generate_list_of_wrong_choices(possible_wrong_choices, no_of_wrong_choices):
    """Returns a list of text of wrong_choice text."""

    wrong_choices = random.sample(list(possible_wrong_choices), min(len(possible_wrong_choices), no_of_wrong_choices))

    # Return a list of the text of the wrong choices
    return [wrong_choice.text for wrong_choice in wrong_choices]
