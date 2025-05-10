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
├── adaMedical_App/           # Your application code
│   ├── app/                  # Main application package
│   │   ├── auth/
│   │   ├── users/
│   │   ├── __init__.py
│   │   └── extensions.py
│   ├── migrations/           # Alembic migration scripts
│   ├── .flaskenv             # Flask CLI environment variables
│   ├── config.py
│   ├── app.py                # Application factory (create_app)
│   └── requirements.txt
├── .env                      # Environment variables (you create this)
├── .env.example              # Example environment variables file
├── Dockerfile                # For building Docker images (project root)
├── docker-compose.yml        # For multi-container local development (project root)
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
2.  Create a `.env` file by copying `.env.example` (if provided) or creating it manually.
3.  Populate it with your specific configurations:

    ```env
    # Flask Configuration (for .flaskenv in adaMedical_App or direct use by Docker)
    FLASK_APP=app:create_app()
    FLASK_ENV=development

    # Application Secrets
    SECRET_KEY='your_flask_secret_key_for_sessions_and_csrf'
    JWT_SECRET_KEY='your_jwt_secret_key'

    # Database (MySQL)
    SQLALCHEMY_DATABASE_URI='mysql+mysqlclient://YOUR_DB_USER:YOUR_DB_PASSWORD@127.0.0.1:3306/YOUR_DATABASE_NAME'
    # For Docker Compose, this will be overridden to use the 'db' service by docker-compose.yml if you keep that setting.
    # Example for .env if using Docker Compose for DB connection:
    # SQLALCHEMY_DATABASE_URI=mysql+mysqlclient://${MYSQL_USER:-user}:${MYSQL_PASSWORD:-password}@db:3306/${MYSQL_DATABASE:-appdb}

    # MySQL connection details for docker-compose 'db' service (if used)
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
    *   The `.env` file should be in the **project root** (`your_project_root/`) to be used by Docker Compose.
    *   If you have a `.flaskenv` file inside `adaMedical_App/` for local Flask CLI commands, it will take precedence for those commands.
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

Using Docker is recommended for consistent environments and easier deployment. The `Dockerfile` and `docker-compose.yml` are now located in the project root. The `adaMedical_App/` directory serves as the build context for the application image.

### Dockerfile
A `Dockerfile` is provided in the project root (`./Dockerfile`). It defines a multi-stage build to create an optimized runtime image.

### Building the Docker Image

Navigate to the **project root** (where `./Dockerfile` and `./docker-compose.yml` are located) and run:
```bash
# This command builds the 'app' service defined in docker-compose.yml
docker-compose build app

# Alternatively, to build directly using Docker if not using compose for building:
# docker build -t integrated-business-api -f ./Dockerfile ./adaMedical_App
# (The -f specifies the Dockerfile, and the last argument is the build context path)
```
Replace `integrated-business-api` with your desired image name if building manually.

### Running the Docker Container

To run the image built via `docker build` (manual approach):
```bash
docker run -d -p 5000:8000 \
    --name my-business-app \
    --env-file ./.env \ # Pass the .env file from the project root
    # You might still need to explicitly pass secrets or override specific env vars
    # if they are not suitable for direct inclusion in .env or for the Docker environment.
    # e.g., -e FLASK_ENV='production' \
    # -e SQLALCHEMY_DATABASE_URI='mysql+mysqlclient://USER:PASS@your_db_host_accessible_from_docker:3306/DB_NAME' \
    # -e GOOGLE_REDIRECT_URI='http://your_app_public_url/api/v1/auth/google/callback' \
    integrated-business-api # Or your custom image name
```
**Notes for `docker run`:**
*   `--env-file ./.env`: Loads variables from the `.env` file located in the project root.
*   Ensure variables in `.env` like `SQLALCHEMY_DATABASE_URI` are set correctly for Docker (e.g., pointing to a networked DB or `host.docker.internal` if applicable).
*   `GOOGLE_REDIRECT_URI` should be your publicly accessible URL.

### Docker Compose (Recommended for Local Docker Development & Full Stack)

The `./docker-compose.yml` file simplifies managing your application and a database container together.

To use Docker Compose (ensure you are in the **project root**):
1.  **Create/Update `.env` file:** Make sure your `./.env` file in the project root contains all necessary variables, including those for the `db` service (like `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, etc.) and for the `app` service (like `SECRET_KEY`, `JWT_SECRET_KEY`, and a `SQLALCHEMY_DATABASE_URI` that points to the `db` service, e.g., `mysql+mysqlclient://${MYSQL_USER}:${MYSQL_PASSWORD}@db:3306/${MYSQL_DATABASE}`).
2.  **Start services:**
    ```bash
    docker-compose up --build
    ```
    The `--build` flag rebuilds the image if the `Dockerfile` or context (`adaMedical_App/`) has changed.
3.  **Run migrations (if needed):**
    If your application doesn't run migrations on startup automatically, you can execute them in the running service:
    ```bash
    docker-compose exec app flask db upgrade
    ```

## API Documentation
Once the application is running (either locally or via Docker), OpenAPI/Swagger documentation is available at:
`/api/v1/doc/`

## Authentication & Authorization
(This section remains the same as before)

## Initial Data Setup
(This section remains the same, but commands like `flask shell` should be run within the `adaMedical_App` directory for local setup, or via `docker-compose exec app flask shell` for Docker setups.)

## Running Tests (Placeholder)
(This section remains the same. Tests would be run from within the `adaMedical_App` directory or via Docker exec.)

---
This README should provide a comprehensive guide for developers.
