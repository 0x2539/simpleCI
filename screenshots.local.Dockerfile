FROM python:3.7.2

ENV SCREENSHOTS_PATH="/screenshots/{}"
ENV FILE_SERVER_PATH="/screenshots/"
WORKDIR /app

COPY ./requirements.txt         ./requirements.txt
RUN pip install -r requirements.txt

COPY ./src/screenshots_local    ./src/screenshots_local

CMD python -m http.server --directory $FILE_SERVER_PATH $FILE_SERVER_PORT & gunicorn -c src/screenshots_local/gunicorn_conf.py src.screenshots_local.wsgi:app
