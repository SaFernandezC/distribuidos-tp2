FROM rabbitmq:3.9.16-management-alpine
RUN apk update && apk add curl
COPY 20-logging.conf /etc/rabbitmq/conf.d
