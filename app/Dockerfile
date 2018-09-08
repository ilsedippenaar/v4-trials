FROM python:3.7.0-alpine

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN apk update \
    && apk add libpq \
    && apk add --virtual build-deps gcc python3-dev musl-dev postgresql-dev \
    && pip install -r requirements.txt \
    && apk del build-deps
COPY . /app

CMD ["python", "server.py"]
