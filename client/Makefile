SHELL := /bin/bash
PWD := $(shell pwd)

default: build

all:

docker-image:
	docker build -f ./Dockerfile -t "client:latest" .
.PHONY: docker-image

docker-run: docker-image
	docker run --network=distribuidos-tp1_testing_net --name client client:latest
.PHONY: docker-run

docker-down:
	docker stop client
	docker rm client
.PHONY: docker-down

docker-logs:
	docker logs client
.PHONY: docker-logs

docker-compose-up: docker-image
	docker compose -f docker-compose-client.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-down:
	docker compose -f docker-compose-client.yaml stop -t 1
	docker compose -f docker-compose-client.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker compose -f docker-compose-client.yaml logs -f
.PHONY: docker-compose-logs