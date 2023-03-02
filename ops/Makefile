up:
	docker compose up --remove-orphans web

build:
	docker compose build

bash:
	docker compose run --rm web bash

shell:
	docker compose run --rm web python manage.py shell

down:
	docker compose down -v --remove-orphans

dbshell:
	docker compose run --rm web python manage.py dbshell

web:
	docker compose up web

prepare:
	docker compose run --rm web python manage.py migrate && \
	docker compose run --rm web python manage.py collectstatic --no-input && \
	docker compose run --rm web sh -c "echo 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\"admin\", \"admin@myproject.com\", \"password\")' | python manage.py shell"
