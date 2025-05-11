# Integrated Business Operations Platform API

This is the Python Flask backend for the Integrated Business Operations Platform. It provides a RESTful JSON API to manage orders, invoicing, payments, contacts, organizations, inventory, deliveries, purchases, expenditures, user access, and maintain a comprehensive audit trail.

## Table of Contents

1.  [Features](#features)
2.  [Technology Stack](#technology-stack)
3.  [Project Structure](#project-structure)
4.  [Local Development Setup](#local-development-setup)
    *   [Prerequisites](#prerequisites)
    *   [Environment Variables](#environment-variables)
    *   [Database Setup](#database-setup)
    *   [Running the Application](#running-the-application)
5.  [Docker Deployment](#docker-deployment)
    *   [Building the Docker Image](#building-the-docker-image)
    *   [Running the Docker Container](#running-the-docker-container)
    *   [Docker Compose (Recommended)](#docker-compose-recommended)
6.  [API Documentation](#api-documentation)
7.  [Authentication & Authorization](#authentication--authorization)
8.  [Initial Data Setup](#initial-data-setup)
9.  [Running Tests (Placeholder)](#running-tests-placeholder)

## Features

*   User Management (Email/Password & Google SSO) with RBAC (Admin, Sales, Operations, Accounts roles)
*   Product & Multi-Location Inventory Management (SKUs, Batches, Serials)
*   Contact & Organization Management
*   Order Management (Quotes, Orders)
*   Invoice & Credit Note Management
*   Payment Tracking
*   Delivery Management (Outsourced, PoD)
*   Purchase Order & Expenditure Tracking
*   Comprehensive Audit Trail for critical operations
*   Multi-Currency Support (SGD & IDR, handled as distinct labels)
*   RESTful JSON API with versioning (`/api/v1/`)

## Technology Stack

*   **Backend Framework:** Python 3.x with Flask
*   **Database:** Google Cloud SQL (MySQL)
*   **ORM:** Flask-SQLAlchemy
*   **Database Migrations:** Flask-Migrate (Alembic)
*   **API Specification:** Flask-RESTx (OpenAPI/Swagger generation)
*   **Authentication:** Flask-JWT-Extended (Token-based), Authlib (Google OAuth 2.0)
*   **Serialization/Validation:** Marshmallow, Flask-Marshmallow
*   **CORS:** Flask-CORS
*   **Password Hashing:** bcrypt
*   **Deployment (recommended):** Docker, Gunicorn

## Project Structure

```
your_project_root/
├── adaMedical_App/           # Your application code (remains the primary source for the app)
│   ├── app/                  # Main application package
│   │   ├── auth/
│   │   ├── users/
│   │   ├── __init__.py
│   │   └── extensions.py
│   ├── migrations/           # Alembic migration scripts
│   ├── .flaskenv             # Flask CLI environment variables
│   ├── config.py
│   ├── app.py                # Application factory (create_app)
│   └── requirements.txt      # Python dependencies, used by Docker build in project root context
├── docker/                   # Docker-related files
│   ├── Dockerfile            # For building Docker images
│   └── docker-compose.yml    # For multi-container local development
├── .env                      # Environment variables (you create this in project root)
├── .env.example              # Example environment variables file
└── README.md                 # This file
```

## Local Development Setup

These instructions are for setting up the project directly on your machine within the `adaMedical_App` directory. For Docker-based setup, see the [Docker Deployment](#docker-deployment) section.

### Prerequisites

*   Python 3.8+
*   MySQL client libraries
*   Access to a MySQL database instance
*   (Optional but Recommended) [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/mysql/connect-auth-proxy)

### Environment Variables

1.  Navigate to the project root (`your_project_root/`).
2.  Create a `.env` file by copying `.env.example` (if provided) or creating it manually. This file should reside in the **project root**.
3.  Populate it with your specific configurations:

    ```env
    # Flask Configuration (for .flaskenv in adaMedical_App or direct use by Docker)
    FLASK_APP=app:create_app() # Points to adaMedical_App/app.py
    FLASK_ENV=development

    # Application Secrets
    SECRET_KEY='your_flask_secret_key_for_sessions_and_csrf'
    JWT_SECRET_KEY='your_jwt_secret_key'

    # Database (MySQL)
    # For local non-Docker: SQLALCHEMY_DATABASE_URI='mysql+mysqlclient://YOUR_DB_USER:YOUR_DB_PASSWORD@127.0.0.1:3306/YOUR_DATABASE_NAME'
    # For Docker Compose (points to 'db' service):
    SQLALCHEMY_DATABASE_URI=mysql+mysqlclient://${MYSQL_USER:-user}:${MYSQL_PASSWORD:-password}@db:3306/${MYSQL_DATABASE:-appdb}

    # MySQL connection details for docker-compose 'db' service (used by docker/docker-compose.yml)
    MYSQL_ROOT_PASSWORD=rootpassword
    MYSQL_DATABASE=appdb
    MYSQL_USER=user
    MYSQL_PASSWORD=password

    # Google OAuth Credentials
    GOOGLE_CLIENT_ID='your_google_client_id.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET='your_google_client_secret_key'
    GOOGLE_REDIRECT_URI='http://localhost:5000/api/v1/auth/google/callback' # Adjust if your app runs on a different port/domain

    # Application Behavior
    DEFAULT_CURRENCY='SGD'
    DEFAULT_USER_ROLE='User'
    ```

    **Important:**
    *   The `.env` file MUST be in the **project root** (`your_project_root/`) to be correctly used by `docker-compose.yml` (which is in `docker/docker-compose.yml` and references `../.env`).
    *   If you have a `.flaskenv` file inside `adaMedical_App/` for local Flask CLI commands, it will take precedence for those commands when running Flask directly.
    *   Ensure `GOOGLE_REDIRECT_URI` matches your Google Cloud Console settings.

### Database Setup (Inside `adaMedical_App`)

1.  **Navigate to your application directory:**
    ```bash
    cd adaMedical_App
    ```
2.  **Ensure MySQL Server is Running** (as described previously).
3.  **Initialize Migrations (if not already done):**
    ```bash
    flask db init
    ```
4.  **Create and Apply Migrations:**
    ```bash
    flask db migrate -m "Descriptive message"
    flask db upgrade
    ```

### Running the Application (Local Development from `adaMedical_App`)

1.  Navigate to your application directory:
    ```bash
    cd adaMedical_App
    ```
2.  Run:
    ```bash
    flask run
    ```
    The application will usually be available at `http://localhost:5000`.

## Docker Deployment

Using Docker is recommended for consistent environments and easier deployment. The `Dockerfile` and `docker-compose.yml` are now located in the `docker/` directory.
The `docker-compose.yml` is configured to use the **project root (`../` relative to `docker/docker-compose.yml`) as the build context**. This means the `Dockerfile` (located at `docker/Dockerfile` but referenced correctly by the compose file) will operate as if it's in the project root, correctly finding `requirements.txt` and `adaMedical_App/` at that level.

### Dockerfile
A `Dockerfile` is provided in `docker/Dockerfile`. It defines a multi-stage build to create an optimized runtime image. The paths inside the `Dockerfile` (e.g., `COPY requirements.txt .`, `COPY adaMedical_App /app/adaMedical_App`) are relative to the build context (project root).

### Building the Docker Image

Navigate to the **`docker/` directory** (where `docker-compose.yml` is located) and run:
```bash
# This command builds the 'app' service defined in docker-compose.yml
# It uses the context '..' (project root) as specified in docker-compose.yml
docker-compose build app

# Alternatively, to build directly using Docker (less common if using compose):
# 1. Navigate to the project root: cd .. (if you are in docker/) or cd your_project_root
# 2. Run the build command:
# docker build -t integrated-business-api -f ./docker/Dockerfile .
# (The -f specifies the Dockerfile path, and the last argument '.' is the build context - project root)
```
Replace `integrated-business-api` with your desired image name if building manually.

### Running the Docker Container

To run an image built manually via `docker build` (this assumes the image was built using the project root as context as shown above):
```bash
# Ensure you are in the project root when running this, so './.env' is found.
docker run -d -p 5000:8000 \
    --name my-business-app \
    --env-file ./.env \ # Pass the .env file from the project root
    # You might still need to explicitly pass secrets or override specific env vars
    # e.g., -e FLASK_ENV='production' \
    # -e SQLALCHEMY_DATABASE_URI='mysql+mysqlclient://USER:PASS@your_db_host_accessible_from_docker:3306/DB_NAME' \
    # -e GOOGLE_REDIRECT_URI='http://your_app_public_url/api/v1/auth/google/callback' \
    integrated-business-api # Or your custom image name
```
**Notes for `docker run`:**
*   `--env-file ./.env`: Loads variables from the `.env` file located in the project root.
*   Ensure variables in `.env` like `SQLALCHEMY_DATABASE_URI` are set correctly for Docker (e.g., pointing to a networked DB or using `host.docker.internal` if your DB is on the host and you're on Docker Desktop). The provided `docker-compose.yml` handles this by setting `SQLALCHEMY_DATABASE_URI` to use the `db` service name.
*   `GOOGLE_REDIRECT_URI` should be your publicly accessible URL when deployed.

### Docker Compose (Recommended for Local Docker Development & Full Stack)
The `docker/docker-compose.yml` file simplifies managing your application and a database container together.

To use Docker Compose:
1.  **Navigate to the `docker/` directory.**
2.  **Ensure `.env` file is in project root:** Make sure your `.env` file is in the **project root** (`../.env` relative to `docker/docker-compose.yml`). It should contain all necessary variables, including those for the `db` service (like `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, etc.) and for the `app` service (like `SECRET_KEY`, `JWT_SECRET_KEY`). The `SQLALCHEMY_DATABASE_URI` in `.env` should be configured to point to the `db` service as shown in the example `.env` content above.
3.  **Start services:**
    ```bash
    docker-compose up --build
    ```
    The `--build` flag rebuilds the image if the `Dockerfile` (in `docker/Dockerfile`) or the build context (`../` - the project root) has changed.
4.  **Run migrations (if needed):**
    If your application doesn't run migrations on startup automatically, you can execute them in the running service (run from the `docker/` directory):
    ```bash
    docker-compose exec app flask db upgrade
    ```

## API Documentation
Once the application is running (either locally or via Docker), OpenAPI/Swagger documentation is available at:
`/api/v1/doc/` (assuming the application is mapped to the root of the host port, e.g. `http://localhost:5000/api/v1/doc/`)

## Authentication & Authorization
(This section remains the same as before - details depend on your implementation within `adaMedical_App`)

## Initial Data Setup
(This section remains the same. Commands like `flask shell` should be run within the `adaMedical_App` directory for local setup. For Docker setups, use `docker-compose exec app flask shell` from the `docker/` directory.)

## Running Tests (Placeholder)
(This section remains the same. Tests would be run from within the `adaMedical_App` directory or via `docker-compose exec app <your_test_command>` from the `docker/` directory.)

---
This README should provide a comprehensive guide for developers.

Force Git
