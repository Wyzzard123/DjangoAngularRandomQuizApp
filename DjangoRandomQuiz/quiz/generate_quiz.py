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







