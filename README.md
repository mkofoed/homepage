[![CI](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml/badge.svg)](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml)

# Django Project with Docker Compose and GitHub Actions for CD.

This is a Django project that is running in a Docker container on a DigitalOcean droplet. It uses a GitHub action for image building and deployment.

## Description
This repository contains the source code for my homepage ([https://mkofoed.dk]()). It is a Django project that runs in a Docker container on a DigitalOcean droplet. The project is designed to be scalable and easy to deploy.

For deployment, this repository is set up with a GitHub action for image building and deployment to a remote machine.

# Technical implementation
## Dockerfile
The Dockerfile `ops/Dockerfile` sets up a base image for both development and production environments using the Python 3.11 Alpine image. It installs Poetry as a dependency manager and sets up a working directory for the application.

Lastly, it copies the application code into the /homepage directory within the container, making it ready for use in both development and production environments.

## Development setup:
The Docker Compose file `ops/docker-compose.yml` sets up a development environment consisting of two services: a Django web application and a PostgreSQL database. The Django app runs on port 5000 and is built using the provided Dockerfile. It has a working directory and a mounted volume to enable live code updates. The PostgreSQL service uses the version 15 image and is configured with environment variables for database credentials. The web app is dependent on the database, ensuring it's running before starting the app. A named volume is created for PostgreSQL to persist data across container restarts.

## Production setup:
The Docker Compose file `ops/docker-compose.production.yml` sets up a production environment with three services: a Django web application, an Nginx web server, and a PostgreSQL database.

The Django app uses a specific image built from the latest GitHub commit SHA, runs the Gunicorn server on port 5000, and has working directories and volumes for static and media files. It depends on the PostgreSQL database and Nginx server to ensure they are running before starting the app.

The Nginx service uses the jonasal/nginx-certbot:4.2-alpine image and is configured to automatically manage SSL certificates using Certbot. It has volumes for static and media files, as well as Nginx configurations and SSL certificates. It listens on ports 80 and 443 for HTTP and HTTPS traffic.

The PostgreSQL service uses the version 15 image and is configured with environment variables for database credentials. A named volume is created for PostgreSQL to persist data across container restarts.

Additional named volumes are created for static files, media files, and Nginx SSL certificates to ensure data persistence and proper configuration in the production environment.

## Deployment:
Deploying this project is done with a GitHub Action called "Build and Deploy". It does the following:

1. **Trigger**: The workflow can be run manually from the Actions tab.
2. **Environment Variables**: Set the IMAGE_NAME environment variable to "homepage" (or whatever the image is called in Docker Hub)
3. **Jobs**: There are two jobs - one for building and pushing the image, and one for deploying it on the remote machine.
   1. **build_and_push**:
      1. Checkout the repository.
      2. Build the container image using the Dockerfile in the "ops" directory.
      3. Log in to Docker Hub.
      4. Push the built image to Docker Hub with the current GitHub commit SHA as the tag.
   2. **deploy** (depends on build_and_push job):
      1. Checkout the repository.
      2. Transfer the repository content to a remote machine.
      3. Create a .env file with environment variables from GitHub secrets.
      4. Copy the .env file to the remote machine.
      5. Deploy to a Digital Ocean droplet via SSH action:
         1. Change to the "ops" directory.
         2. Rename the production docker-compose file.
         3. Rename the .env file.
         4. Log in to Docker Hub.
         5. Pull the latest image from Docker Hub.
         6. Start and build containers using the docker-compose.yml file.
         7. Run the "collectstatic" Django command.
         8. Run the "migrate" Django command.
         9. Restart the containers.

# License
This project is licensed under the MIT License - see the `LICENSE` file for details.
