FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
RUN pip install --upgrade pip
COPY ./req.txt .
RUN pip install -r req.txt
COPY init.sql /docker-entrypoint-initdb.d/init.sql
COPY . .