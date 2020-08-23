from django.contrib.auth.models import User
from django.db import models


class Topic(models.Model):
    """
    A topic which can contain many questions. When creating a question, we will link it to a topic (or many topics).
    """
    creator = models.ForeignKey(User, verbose_name="Creator", related_name="topics", on_delete=models.CASCADE)
    name = models.CharField(max_length=256, verbose_name="Topic Name")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        default_related_name = "topics"
        unique_together = [["creator", "name"]]


class Answer(models.Model):
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


class Question(models.Model):
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



