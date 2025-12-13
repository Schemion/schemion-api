FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic1 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* 

WORKDIR /app

ENV PYTHONPATH=/app

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

COPY . .


