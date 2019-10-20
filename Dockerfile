FROM python:3.7-alpine
# A side effect of using alpine is you must build psycopg2 from source
RUN pip install --upgrade pip
RUN apk update && apk add alpine-sdk postgresql-dev netcat-openbsd
ENV LIBRARY_PATH=/lib:/usr/lib
COPY . /engage-scraper
WORKDIR /engage-scraper
RUN pip install -r engage_scraper/requirements.txt