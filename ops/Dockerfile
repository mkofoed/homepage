FROM python:3.11-bullseye

# ----------------- Install Packages and Postgres Client -----------------
RUN apt update \
        && apt install -y --no-install-recommends lsb-release  \
        && echo "deb http://apt.postgresql.org/pub/repos/apt `lsb_release -cs`-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
        && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
        && apt update \
        && apt install -y --no-install-recommends postgresql-client-10 postgresql-client-15 \
        && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==1.4.0"

WORKDIR /homepage
COPY poetry.lock pyproject.toml /homepage/ops/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && cd ./ops \
  && poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi

COPY . /homepage/
