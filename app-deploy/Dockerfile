FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src/api/ /app/api/
COPY src/templates/ /app/templates/

EXPOSE 5000