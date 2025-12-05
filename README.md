# Personal Homepage

[![Deploy to VM](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml/badge.svg)](https://github.com/mkofoed/homepage/actions/workflows/deploy.yml)

A personal homepage application built with Django, Docker, and PostgreSQL.

## Tech Stack

- **Backend**: Django 6.0
- **Database**: PostgreSQL 18
- **Containerization**: Docker & Docker Compose
- **Web Server**: Gunicorn & Nginx
- **Dependencies**: uv (fast Python package manager)
- **Deployment**: Hetzner VM (via GitHub Actions)

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Development Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/mkofoed/homepage.git
    cd homepage
    ```

2.  **Create environment file:**

    Copy the example environment file to `.env`:

    ```bash
    cp .env.example .env
    ```

    *Note: Adjust the values in `.env` if necessary.*

3.  **Build and run the containers:**

    ```bash
    docker-compose up --build
    ```

    The application will be available at `http://localhost:8000`.

4.  **Accessing the application:**
    - Homepage: `http://localhost:8000/`
    - Admin Panel: `http://localhost:8000/admin/`

## Project Structure

- `config/`: Django project configuration settings.
- `core/`: Core application logic.
- `blog/`: Blog application.
- `nginx/`: Nginx configuration for production.
- `pyproject.toml`: Python dependencies (managed with uv).
- `docker-compose.yml`: Docker Compose configuration for development.
- `docker-compose.prod.yml`: Docker Compose configuration for production.

## Deployment

The application is deployed to a **Hetzner VM** using GitHub Actions for continuous delivery.

### Server Prerequisites

The target server must have Docker and Docker Compose installed. We provide a script to automate the initial provisioning.

### GitHub Secrets

To enable automated deployment, configure the following secrets in your GitHub repository settings (**Settings** > **Secrets and variables** > **Actions**):

| Secret Name | Description |
| :--- | :--- |
| `DROPLET_IP` | The public IP address of your Hetzner server. |
| `DROPLET_USER` | The SSH username (usually `root`). |
| `SSH_PRIVATE_KEY` | The private SSH key for authenticating with the server. |
| `DOCKER_USERNAME` | Your Docker Hub username. |
| `DOCKER_PASSWORD` | Your Docker Hub access token or password. |
| `ENV_FILE` | The **full content** of your production `.env` file. |

### Initial Server Setup

We have a script `setup_hetzner.sh` that automates the server provisioning (installing Docker, UFW, etc.).

1.  **Copy the script to your server:**
    ```bash
    scp setup_hetzner.sh root@<your-server-ip>:~/
    ```

2.  **SSH into your server:**
    ```bash
    ssh root@<your-server-ip>
    ```

3.  **Run the setup script:**
    ```bash
    chmod +x setup_hetzner.sh
    ./setup_hetzner.sh
    ```

4.  **Clone the repository:**
    ```bash
    git clone https://github.com/mkofoed/homepage.git ~/homepage
    ```

5.  **Initialize HTTPS:**
    The Nginx container (`jonasal/nginx-certbot`) handles SSL certificates automatically via Let's Encrypt. Ensure your DNS records (A and CNAME) are pointing to the server IP before starting the containers.

### Automated Deployment

Deployment is triggered automatically when you push changes to the `main` branch. The GitHub Action workflow (`.github/workflows/deploy.yml`) performs the following steps:

1.  **Build & Push:** Builds the Docker image and pushes it to Docker Hub.
2.  **Deploy:**
    -   Connects to the server via SSH.
    -   Navigates to the project directory (`~/homepage`).
    -   Injects the `.env` file from the `ENV_FILE` secret.
    -   Executes the `deploy.sh` script to pull the new image and restart containers.

### Manual Deployment

If you need to deploy manually without pushing to GitHub:

1.  **SSH into the server.**
2.  **Navigate to the project directory:**
    ```bash
    cd ~/homepage
    ```
3.  **Run the deployment script:**
    ```bash
    ./deploy.sh
    ```

The `deploy.sh` script handles pulling the latest code, rebuilding Docker images, running migrations, and collecting static files.

## Administration

### Create Superuser

To create a superuser for the Django admin panel:

**Local Development:**
```bash
docker-compose exec web python manage.py createsuperuser
```

**Production:**
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```
