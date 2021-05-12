#!/bin/sh
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
python3 manage.py shell -c "exec(\"from django.contrib.auth import get_user_model\\nif not get_user_model().objects.filter(username='admin'):\\n get_user_model().objects.create_superuser('admin', 'admin@avodaq.com', 'Cisco1234*')\")"

# Create Quiz application for OAuth and hardcode client ID to 'QuizAppClientID'
python3 manage.py shell -c "exec(\"from django.contrib.auth import get_user_model\\nfrom oauth2_provider.models import Application, AbstractApplication\\nif not Application.objects.filter(client_id='QuizAppClientID'):\\n Application.objects.create(client_id='QuizAppClientID', user=get_user_model().objects.get(username='admin'), authorization_grant_type=AbstractApplication.GRANT_PASSWORD, name='QuizApp', client_type=AbstractApplication.CLIENT_PUBLIC)\")"

gunicorn -w 4 -b 0.0.0.0:8000 DjangoRandomQuiz.wsgi:application
