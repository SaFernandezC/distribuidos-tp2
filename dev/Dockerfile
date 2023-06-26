FROM python:3.9.7-slim

RUN pip install --upgrade pip
RUN pip3 install pika
RUN pip3 install python-dotenv
RUN pip3 install ujson
RUN pip3 install docker

COPY . /

CMD ["python3", "./main.py"]