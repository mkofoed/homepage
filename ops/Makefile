up:
	docker compose up -d

build:
	docker compose build

sh:
	docker compose run --rm web sh

shell:
	docker compose run --rm web python manage.py shell

down:
	docker compose down -v --remove-orphans

prune:
	docker system prune --all --volumes --force

restart:
	docker compose run --rm web python manage.py migrate && \
	docker compose run --rm web python manage.py collectstatic --no-input && \
	docker compose restart web

mm:
	docker compose run --rm web python manage.py makemigrations

migrate:
	docker compose run --rm web python manage.py migrate

dbshell:
	docker compose run --rm web python manage.py dbshell
