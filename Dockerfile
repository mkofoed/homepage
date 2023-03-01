FROM python:3.11-bullseye

# ----------------- Install Packages and Postgres Client -----------------
RUN apt update \
        && apt install -y --no-install-recommends lsb-release  \
        && echo "deb http://apt.postgresql.org/pub/repos/apt `lsb_release -cs`-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
        && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
        && apt update \
        && apt install -y --no-install-recommends postgresql-client-10 postgresql-client-15 \
        && rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /homepage

RUN pip install "poetry==1.4.0"

# workdir is the repo name
WORKDIR /homepage

COPY poetry.lock pyproject.toml /homepage/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi


COPY . /homepage

RUN python manage.py collectstatic --noinput