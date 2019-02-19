FROM python:3.7.2

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY ./src/ci           ./src/ci

CMD gunicorn -c src/ci/gunicorn_conf.py src.ci.wsgi:app
