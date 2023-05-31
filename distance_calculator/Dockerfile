FROM python:3.9.7-slim

RUN pip install --upgrade pip
RUN pip3 install pika python-dotenv haversine
RUN pip3 install ujson

COPY distance_calculator /
COPY common /common

CMD ["python3", "./main.py"]