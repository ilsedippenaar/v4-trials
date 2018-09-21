FROM python:3.7.0-alpine

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN apk update \
    && apk add libpq pcre-dev \
    && apk add --virtual build-deps \
        gcc \
        musl-dev \
        build-base \
        linux-headers \
        python3-dev \
        postgresql-dev \
    && pip install -r requirements.txt \
    && apk del build-deps
COPY . /app

CMD ["uwsgi", "--ini", "uwsgi.ini", "--need-app"]
