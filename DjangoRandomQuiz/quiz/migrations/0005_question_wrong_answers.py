# Generated by Django 3.1 on 2021-05-05 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_quizattempt_quiz_attempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='wrong_answers',
            field=models.ManyToManyField(related_name='wrong_questions', to='quiz.Answer'),
        ),
    ]