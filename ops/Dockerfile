FROM python:3.11-alpine

RUN pip install "poetry==1.4.0"

WORKDIR /homepage
COPY poetry.lock pyproject.toml /homepage/ops/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && cd ./ops \
  && poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi

COPY . /homepage/
