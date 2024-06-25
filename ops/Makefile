up:
	echo "Starting services..." && \
	docker compose -f docker-compose.yml up -d --build && \
	echo "Services started successfully"

build:
	echo "Building services..." && \
	docker compose build && \
	echo "Services built successfully"

sh:
	docker compose run --rm web sh

shell:
	docker compose run --rm web python manage.py shell

down:
	echo "Stopping services..." && \
	docker compose down -v --remove-orphans && \
	echo "Services stopped successfully"

prune:
	echo "Pruning docker system..." && \
	docker system prune -a -f && \
	echo "Docker system pruned successfully"

restart:
	echo "Restarting web service..." && \
	docker compose restart web && \
	echo "Web service restarted successfully"

mm:
	echo "Creating migrations..." && \
	docker compose run --rm web python manage.py makemigrations
	echo "Migrations created successfully"

migrate:
	echo "Migrating database..." && \
	docker compose run --rm web python manage.py migrate && \
	echo "Database migrated successfully"

dbshell:
	echo "Connecting to database..." && \
	docker compose run --rm web python manage.py dbshell && \
	echo "Connected to database successfully"

collectstatic:
	if [ ! -d /homepage/static ]; then\
		mkdir /homepage/static;\
	fi && \
	docker compose run web python manage.py collectstatic --no-input

deploy: up collectstatic migrate restart prune
	echo "Deployed successfully"
