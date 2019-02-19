FROM python:3.7.2

WORKDIR /app

COPY ./requirements.txt     ./requirements.txt
RUN pip install -r requirements.txt

COPY ./src/screenshots_s3   ./src/screenshots_s3

CMD gunicorn -c src/screenshots_s3/gunicorn_conf.py src.screenshots_s3.wsgi:app
