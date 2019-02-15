FROM python:3.7.2

ENV SCREENSHOTS_PATH="/screenshots/{}"
ENV SERVE_PATH="/screenshots/"
WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY ./src              ./src

#CMD flask run --host=0.0.0.0 --port=$PORT
CMD python -m http.server --directory $SERVE_PATH $SERVE_PORT & gunicorn -c src/gunicorn_conf.py src.wsgi_screenshots:app
