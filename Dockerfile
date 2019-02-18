FROM python:3.7.2

ENV SCREENSHOTS_PATH="/screenshots/{}"
ENV FILE_SERVER_PATH="/screenshots/"
WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY ./src              ./src

CMD python -m http.server --directory $FILE_SERVER_PATH $FILE_SERVER_PORT & gunicorn -c src/gunicorn_conf.py src.wsgi_screenshots:app
