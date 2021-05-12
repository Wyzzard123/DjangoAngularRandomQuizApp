FROM python:alpine3.13

WORKDIR /app

COPY requirements.txt .

# Need to download postgres beforehand so that we can use pip to install psycopg2-binary==2.8.6
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN python3 -m pip install --no-cache-dir -r requirements.txt

RUN rm -rf /root/.cache/pip src
COPY . .
RUN chmod +x run_django.sh

CMD ["/bin/sh", "-c", "./run_django.sh"]
