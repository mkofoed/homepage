# Personal Homepage

A personal homepage application built with Django, Docker, and PostgreSQL.

## Tech Stack

- **Backend**: Django 5.2
- **Database**: PostgreSQL 18
- **Containerization**: Docker & Docker Compose
- **Web Server**: Gunicorn & Nginx
- **Deployment**: DigitalOcean (via GitHub Actions)

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Development Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
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
- `blog/`: Blog application (if applicable).
- `nginx/`: Nginx configuration for production.
- `docker-compose.yml`: Docker Compose configuration for development.
- `docker-compose.prod.yml`: Docker Compose configuration for production.

## Deployment

The application is deployed to a DigitalOcean droplet using GitHub Actions for continuous delivery.

### Server Prerequisites

The target server (e.g., DigitalOcean Droplet) must have the following installed:
- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

### GitHub Secrets

To enable automated deployment, configure the following secrets in your GitHub repository settings (**Settings** > **Secrets and variables** > **Actions**):

| Secret Name | Description |
| :--- | :--- |
| `DROPLET_IP` | The public IP address of your server. |
| `DROPLET_USER` | The SSH username (usually `root`). |
| `SSH_PRIVATE_KEY` | The private SSH key for authenticating with the server. |
| `DOCKER_USERNAME` | Your Docker Hub username. |
| `DOCKER_PASSWORD` | Your Docker Hub access token or password. |
| `ENV_FILE` | The **full content** of your production `.env` file. |

### Initial Server Setup

Before the first deployment, you need to manually set up the server:

1.  **SSH into your server:**
    ```bash
    ssh root@<your-droplet-ip>
    ```

2.  **Clone the repository:**
    ```bash
    git clone <repository-url> homepage
    cd homepage
    ```
    *Note: The GitHub Action expects the directory to be named `homepage`.*

3.  **Initialize HTTPS (One-time setup):**
    Edit the `init-letsencrypt.sh` file to set your email address, then run it:
    ```bash
    nano init-letsencrypt.sh
    chmod +x init-letsencrypt.sh
    ./init-letsencrypt.sh
    ```
    *This script generates the initial SSL certificates required for Nginx to start.*

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
# Personal Homepage

A personal homepage application built with Django, Docker, and PostgreSQL.

## Tech Stack

- **Backend**: Django 5.2
- **Database**: PostgreSQL 18
- **Containerization**: Docker & Docker Compose
- **Web Server**: Gunicorn & Nginx
- **Deployment**: DigitalOcean (via GitHub Actions)

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Development Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
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
- `blog/`: Blog application (if applicable).
- `nginx/`: Nginx configuration for production.
- `docker-compose.yml`: Docker Compose configuration for development.
- `docker-compose.prod.yml`: Docker Compose configuration for production.

## Deployment

The application is deployed to a DigitalOcean droplet using GitHub Actions for continuous delivery.

### Server Prerequisites

The target server (e.g., DigitalOcean Droplet) must have the following installed:
- [Docker](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

### GitHub Secrets

To enable automated deployment, configure the following secrets in your GitHub repository settings (**Settings** > **Secrets and variables** > **Actions**):

| Secret Name | Description |
| :--- | :--- |
| `DROPLET_IP` | The public IP address of your server. |
| `DROPLET_USER` | The SSH username (usually `root`). |
| `SSH_PRIVATE_KEY` | The private SSH key for authenticating with the server. |
| `DOCKER_USERNAME` | Your Docker Hub username. |
| `DOCKER_PASSWORD` | Your Docker Hub access token or password. |
| `ENV_FILE` | The **full content** of your production `.env` file. |

### Initial Server Setup

Before the first deployment, you need to manually set up the server:

1.  **SSH into your server:**
    ```bash
    ssh root@<your-droplet-ip>
    ```

2.  **Clone the repository:**
    ```bash
    git clone <repository-url> homepage
    cd homepage
    ```
    *Note: The GitHub Action expects the directory to be named `homepage`.*

3.  **Initialize HTTPS (One-time setup):**
    Edit the `init-letsencrypt.sh` file to set your email address, then run it:
    ```bash
    nano init-letsencrypt.sh
    chmod +x init-letsencrypt.sh
    ./init-letsencrypt.sh
    ```
    *This script generates the initial SSL certificates required for Nginx to start.*

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

## Troubleshooting

### Deployment Timeout / Out of Memory

If deployment fails with a timeout or exit code 137 (OOM), your server might be running out of memory. This is common on 512MB droplets.

**Fix: Add Swap Space**

1.  **SSH into the server.**
2.  **Run the swap setup script:**
    ```bash
    chmod +x setup_swap.sh
    sudo ./setup_swap.sh
    ```
    This creates a 1GB swap file to prevent memory exhaustion during builds and migrations.
