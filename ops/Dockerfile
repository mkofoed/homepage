FROM python:3.12-alpine

# Upgrade pip
RUN pip install --upgrade pip
RUN pip install "poetry==1.8.3"

WORKDIR /homepage
COPY poetry.lock pyproject.toml /homepage/ops/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && cd ./ops \
  && poetry install $(test "$ENVIRONMENT" == production && echo "--no-dev") --no-interaction --no-ansi

COPY . /homepage/
