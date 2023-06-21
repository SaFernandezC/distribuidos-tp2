SHELL := /bin/bash
PWD := $(shell pwd)

default: build

all:

docker-image:
	docker build -f ./filter/Dockerfile -t "filter:latest" .
	docker build -f ./accepter/Dockerfile -t "accepter:latest" .
	docker build -f ./joiner/Dockerfile -t "joiner:latest" .
	docker build -f ./date_modifier/Dockerfile -t "date_modifier:latest" .
	docker build -f ./groupby/Dockerfile -t "groupby:latest" .
	docker build -f ./parser/Dockerfile -t "parser:latest" .
	docker build -f ./distance_calculator/Dockerfile -t "distance_calculator:latest" .
	docker build -f ./status_controller/Dockerfile -t "status_controller:latest" .
	docker build -f ./eof_manager/Dockerfile -t "eof_manager:latest" .
	docker build -f ./monitor/Dockerfile -t "monitor:latest" .
	docker build -f ./dev/Dockerfile -t "dev:latest" .
.PHONY: docker-image

docker-compose-up: docker-image
	docker compose -f docker-compose-dev.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-down:
	docker compose -f docker-compose-dev.yaml stop -t 1
	docker compose -f docker-compose-dev.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker compose -f docker-compose-dev.yaml logs -f
.PHONY: docker-compose-logs