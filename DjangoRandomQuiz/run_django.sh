#!/bin/sh
python3 manage.py shell -c "exec(\"from django.contrib.auth import get_user_model\\nif not get_user_model().objects.filter(username='admin'):\\n get_user_model().objects.create_superuser('admin', 'admin@avodaq.com', 'Cisco1234*')\")"
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
gunicorn -w 4 -b 0.0.0.0:8000 DjangoRandomQuiz.wsgi:application