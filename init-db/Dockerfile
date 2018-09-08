FROM python:3.7.0

WORKDIR /init-db
COPY ./requirements.txt /init-db/requirements.txt
RUN apt-get update \
    && pip install -r requirements.txt
COPY . /init-db
CMD ["python", "populate_db.py"]
