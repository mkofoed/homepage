up:
	docker compose up -d

build:
	docker compose build

bash:
	docker compose run --rm web sh

shell:
	docker compose run --rm web python ../manage.py shell

down:
	docker compose down -v --remove-orphans

prune:
	docker system prune --all --volumes --force

restart:
	docker compose run --rm web python manage.py migrate && \
	docker compose run --rm web python manage.py collectstatic --no-input && \
	docker compose restart web

dbshell:
	docker compose run --rm web python manage.py dbshell

prepare:
	docker compose run --rm web python manage.py migrate && \
	docker compose run --rm web python manage.py collectstatic --no-input && \
	docker compose run --rm web sh -c "echo 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\"admin\", \"admin@myproject.com\", \"password\")' | python manage.py shell"
