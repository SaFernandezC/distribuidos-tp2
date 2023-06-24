FROM python:3.9.7-slim

RUN apt-get update && apt-get install -y docker.io
RUN pip install --upgrade pip
RUN pip3 install pika
RUN pip3 install ujson

COPY monitor /
COPY common /common

CMD ["python3", "./main.py"]