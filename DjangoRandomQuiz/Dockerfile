FROM python:alpine3.13

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

RUN rm -rf /root/.cache/pip src
COPY . .
RUN chmod +x run_django.sh

CMD ["/bin/sh", "-c", "./run_django.sh"]
