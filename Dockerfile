FROM python:3.9-alpine AS builder

WORKDIR /app

RUN apk update && apk --no-cache add gcc musl-dev python3-dev libffi-dev openssl-dev cargo

RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
RUN poetry export -f requirements.txt > requirements.txt
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

FROM python:3.9-alpine AS runner

WORKDIR /app
COPY --from=builder --chown=root:root /wheels /wheels

RUN pip install --no-cache --no-deps --no-index /wheels/*
RUN rm -rfv /wheels

COPY . /app

RUN adduser -S rootmebot
RUN chown -R rootmebot /app
USER rootmebot

CMD python rootmebot.py
