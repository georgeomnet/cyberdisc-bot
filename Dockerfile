FROM python:3.7-alpine3.9

RUN apk add --update --no-cache git
RUN apk add --update --no-cache tini
RUN apk add --update --no-cache build-base
RUN apk add --update --no-cache libffi-dev
RUN apk --update --no-cache add imagemagick-dev --repository http://dl-cdn.alpinelinux.org/alpine/v3.9/main/

COPY . /app
WORKDIR /app

RUN pip install poetry==0.12.11
RUN poetry export -f requirements.txt
RUN pip install -r requirements.txt

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python", "-m", "cdbot"]
