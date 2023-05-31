FROM python:3.9.7-slim

RUN pip install --upgrade pip
RUN pip3 install pika
RUN pip3 install ujson

COPY parser /
COPY common /common

CMD ["python3", "./main.py"]