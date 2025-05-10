"""# Integrated Business Operations Platform API

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
/
├── app/                      # Main application package
│   ├── auth/                 # Authentication (SSO, API keys, decorators)
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── routes.py         # Google SSO routes
│   │   └── apikey.py
│   ├── users/                # User and Role management
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── products/             # (Example for future module)
│   ├── orders/               # (Example for future module)
│   ├── __init__.py           # Makes 'app' a package (usually empty or for app-wide setup)
│   ├── extensions.py         # Initializes Flask extensions (db, migrate, jwt, cors, oauth)
│   └── models.py             # (If you have base models or common model utilities) - Currently models are per-module
├── migrations/               # Alembic migration scripts
├── tests/                    # Unit and integration tests (to be developed)
├── .env.example              # Example environment variables file
├── .flaskenv                 # Flask CLI environment variables (e.g., FLASK_APP, FLASK_ENV)
├── config.py                 # Configuration classes (Development, Production, Testing)
├── app.py                    # Application factory (create_app)
├── Dockerfile                # For building Docker images
├── docker-compose.yml        # For multi-container local development/testing (optional)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Local Development Setup

These instructions are for setting up the project directly on your machine. For Docker-based setup, see the [Docker Deployment](#docker-deployment) section.

### Prerequisites

*   Python 3.8+
*   MySQL client libraries (e.g., `libmysqlclient-dev` on Debian/Ubuntu, `mysql-devel` on Fedora/CentOS). This is needed for the `mysqlclient` Python package.
*   Access to a MySQL database instance (e.g., local MySQL server or Google Cloud SQL).
*   (Optional but Recommended) [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/mysql/connect-auth-proxy) if using Google Cloud SQL for local development.

### Environment Variables

1.  Create a `.env` file in the project root by copying `.env.example` (if provided) or creating it manually.
2.  Populate it with your specific configurations:

    ```env
    # Flask Configuration (used by Flask CLI if .flaskenv is not present or for direct script runs)
    FLASK_APP=app:create_app() # Tells Flask CLI how to find the app factory
    FLASK_ENV=development      # Sets mode to development (enables debug mode, etc.)
    # FLASK_DEBUG=1            # Alternative way to enable debug mode

    # Application Secrets (Generate strong random strings for these)
    SECRET_KEY='your_flask_secret_key_for_sessions_and_csrf'
    JWT_SECRET_KEY='your_jwt_secret_key'

    # Database (MySQL - Example for Google Cloud SQL with proxy)
    # Ensure your MySQL server is running and accessible.
    SQLALCHEMY_DATABASE_URI='mysql+mysqlclient://YOUR_DB_USER:YOUR_DB_PASSWORD@127.0.0.1:3306/YOUR_DATABASE_NAME'
    # DEV_DATABASE_URI=... (Optional: if different from SQLALCHEMY_DATABASE_URI for dev)
    # PROD_DATABASE_URI=... (Optional: if different from SQLALCHEMY_DATABASE_URI for prod)

    # Google OAuth Credentials (Obtain from Google Cloud Console)
    GOOGLE_CLIENT_ID='your_google_client_id.apps.googleusercontent.com'
    GOOGLE_CLIENT_SECRET='your_google_client_secret_key'
    # For local dev, this usually points to your local callback.
    # Ensure this exact URI is registered in your Google OAuth Client settings.
    GOOGLE_REDIRECT_URI='http://localhost:5000/api/v1/auth/google/callback'

    # Application Behavior
    DEFAULT_CURRENCY='SGD'
    DEFAULT_USER_ROLE='User' # Default role assigned to new SSO users

    # Logging (Optional)
    # SQLALCHEMY_ECHO=True # To log SQL queries executed by SQLAlchemy (can be verbose)

    # Server Port (Optional, Flask default is 5000)
    # PORT=5000
    ```

    **Important:**
    *   `SECRET_KEY` is critical for session security (used by Authlib for OAuth state).
    *   Ensure `GOOGLE_REDIRECT_URI` exactly matches one of the Authorized Redirect URIs in your Google Cloud Console OAuth 2.0 Client ID settings.

### Database Setup

1.  **Ensure MySQL Server is Running:** Your MySQL database should be accessible. If using Google Cloud SQL for local development, start the Cloud SQL Auth Proxy:
    ```bash
    ./cloud_sql_proxy -instances=YOUR_PROJECT:YOUR_REGION:YOUR_INSTANCE_NAME=tcp:3306
    ```
    Replace placeholders with your actual Google Cloud SQL instance connection name.

2.  **Initialize Migrations (if not already done):**
    This creates the `migrations` directory and Alembic configuration. Only needs to be run once per project.
    ```bash
    flask db init
    ```

3.  **Create and Apply Migrations:**
    Whenever you change your SQLAlchemy models (`app/**/models.py`), you need to generate a new migration script and apply it to the database.
    ```bash
    flask db migrate -m "Descriptive message for your migration (e.g., add_user_table)"
    flask db upgrade
    ```
    To downgrade, you can use `flask db downgrade`.

### Running the Application (Local Development)

```bash
flask run
```
This command will use the `FLASK_APP` and `FLASK_ENV` variables (typically set in `.env` or `.flaskenv`). The application will usually be available at `http://localhost:5000`.

## Docker Deployment

Using Docker is recommended for consistent environments and easier deployment.

### Dockerfile

A `Dockerfile` is provided in the project root. It typically performs the following:
*   Uses an official Python base image.
*   Sets up a working directory.
*   Copies `requirements.txt` and installs dependencies (this layer is cached if `requirements.txt` doesn't change).
*   Copies the rest of the application code.
*   Sets environment variables (though it's better to pass sensitive ones at runtime).
*   Exposes the application port (e.g., 5000 or 8000 for Gunicorn).
*   Specifies the command to run the application (usually Gunicorn for production).

```dockerfile
# Dockerfile (Example - customize as needed)

# 1. Base Image
FROM python:3.9-slim-buster AS builder

# 2. Environment Variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

WORKDIR $APP_HOME

# 3. Install OS-level dependencies for mysqlclient and other build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Application Stage (smaller final image)
FROM python:3.9-slim-buster AS runtime

ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
ENV FLASK_ENV production # Default to production in Docker

WORKDIR $APP_HOME

# Copy installed dependencies from builder stage
COPY --from=builder $APP_HOME $APP_HOME
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Expose port Gunicorn will run on
EXPOSE 8000

# Run database migrations (optional - can be run as a separate step/job in CI/CD)
# ENTRYPOINT ["/bin/bash", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:8000 "app:create_app('production')""]

# Command to run the application using Gunicorn
# Ensure create_app() can be called with 'production' or rely on FLASK_ENV
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--log-level", "info", "app:create_app()"]

```

### Building the Docker Image

Navigate to the project root (where the `Dockerfile` is located) and run:
```bash
docker build -t integrated-business-api .
```
Replace `integrated-business-api` with your desired image name and tag.

### Running the Docker Container

To run the built image:
```bash
docker run -d -p 5000:8000 \
    --name my-business-app \
    -e SECRET_KEY='your_strong_secret_key_for_docker' \
    -e JWT_SECRET_KEY='your_strong_jwt_key_for_docker' \
    -e SQLALCHEMY_DATABASE_URI='mysql+mysqlclient://USER:PASS@your_db_host_accessible_from_docker:3306/DB_NAME' \
    -e GOOGLE_CLIENT_ID='your_google_client_id' \
    -e GOOGLE_CLIENT_SECRET='your_google_secret' \
    -e GOOGLE_REDIRECT_URI='http://your_app_public_url/api/v1/auth/google/callback' \
    # Add other necessary environment variables from your .env file
    # Ensure your FLASK_ENV is set to 'production' if not already in the Dockerfile
    -e FLASK_ENV='production' \
    integrated-business-api
```

**Notes:**
*   `-d`: Runs the container in detached mode.
*   `-p 5000:8000`: Maps port 5000 on your host to port 8000 in the container (Gunicorn's port). Adjust if your Gunicorn port is different.
*   `--name`: Assigns a name to your container.
*   `-e VAR_NAME='value'`: Sets environment variables. **It is crucial to provide all required environment variables, especially secrets and database URIs.**
*   `your_db_host_accessible_from_docker`: This needs to be the hostname or IP address of your MySQL database server that is reachable from within the Docker container. If your DB is also a Docker container on the same network, you can use its service name. For Cloud SQL, you might need to configure serverless VPC access or run the Cloud SQL Proxy in a sidecar container or on the host and expose its port.
*   `GOOGLE_REDIRECT_URI` for Docker deployment should be the publicly accessible URL that Google will redirect to, pointing to your deployed application's callback endpoint.

**Database Migrations with Docker:**
Migrations should ideally be run as a separate step before deploying a new version of the application container, or as an init container in orchestrators like Kubernetes.
If your `CMD` or `ENTRYPOINT` in the Dockerfile runs migrations, ensure:
1.  The database is accessible when the container starts.
2.  Only one instance runs migrations if you scale your application.

### Docker Compose (Recommended for Local Docker Development & Testing)

`docker-compose.yml` can simplify managing multi-container setups (e.g., your app + a MySQL database for testing).

```yaml
# docker-compose.yml (Example)
version: '3.8'

services:
  app:
    build: . # Build from Dockerfile in the current directory
    container_name: business-api-app
    ports:
      - "5000:8000" # Host:Container (Gunicorn port)
    environment:
      # It's often better to use a .env file with Docker Compose
      # Or define them directly here (less secure for secrets)
      - FLASK_ENV=development # Override to development for local compose
      - SECRET_KEY=${SECRET_KEY} # Reads from .env file in the same dir as docker-compose.yml
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - SQLALCHEMY_DATABASE_URI=mysql+mysqlclient://${MYSQL_USER:-user}:${MYSQL_PASSWORD:-password}@db:3306/${MYSQL_DATABASE:-appdb}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI} # Typically http://localhost:5000/api/v1/auth/google/callback for local compose
      # Add other necessary env vars
    volumes:
      - .:/app # Mounts current directory to /app in container for live code reloading (dev only!)
    depends_on:
      db:
        condition: service_healthy # Wait for DB to be ready
    # command: flask db upgrade && flask run --host=0.0.0.0 --port=5000 # For dev with Flask server
    command: gunicorn --bind 0.0.0.0:8000 --workers 1 --reload "app:create_app()" # For dev with Gunicorn and reload

  db:
    image: mysql:8.0
    container_name: business-api-db
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpassword}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-appdb}
      MYSQL_USER: ${MYSQL_USER:-user}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-password}
    ports:
      - "3307:3306" # Expose MySQL on host port 3307 to avoid conflict if local MySQL runs on 3306
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin" ,"ping", "-h", "localhost", "-u$$MYSQL_USER", "-p$$MYSQL_PASSWORD"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  mysql_data:
```

To use with Docker Compose (ensure you have a `.env` file in the same directory as `docker-compose.yml` with the referenced variables):
```bash
docker-compose up --build
```
To run migrations with Docker Compose (if not handled automatically by the app's entrypoint):
```bash
docker-compose exec app flask db upgrade
```

## API Documentation

Once the application is running, OpenAPI/Swagger documentation is available at:
`/api/v1/doc/`

## Authentication & Authorization

*   **Staff Authentication:** Token-based (JWT) via Email/Password or Google SSO (OAuth 2.0).
*   **Server-to-Server:** API Key authentication (via `X-API-KEY` header).
*   **Authorization:** Role-Based Access Control (RBAC). Defined roles: Admin, Sales, Operations/Warehouse, Accounts. Decorators like `@admin_required` and `@role_required([...])` protect endpoints.

## Initial Data Setup

After the first `flask db upgrade`, some initial data like roles might be needed.

1.  **Create Default Roles (Admin, User, etc.):**
    You can use `flask shell` for this:
    ```bash
    flask shell
    ```
    Then in the Python shell:
    ```python
    from app.extensions import db
    from app.users.models import Role
    from flask import current_app

    def create_role_if_not_exists(name):
        if not Role.query.filter_by(name=name).first():
            role = Role(name=name)
            db.session.add(role)
            print(f"Role '{name}' created.")
        else:
            print(f"Role '{name}' already exists.")

    create_role_if_not_exists('Admin')
    create_role_if_not_exists(current_app.config.get('DEFAULT_USER_ROLE', 'User'))
    # Add other roles like 'Sales', 'Operations', 'Accounts'
    # create_role_if_not_exists('Sales')

    db.session.commit()
    print("Roles checked/created.")
    exit()
    ```

2.  **Create Initial Admin User:**
    The first admin user usually needs to be created manually or via a specific script after roles are set up.
    Using `flask shell`:
    ```python
    # In flask shell:
    from app.extensions import db
    from app.users.models import User, Role
    admin_email = 'admin@example.com' # Change as needed
    admin_name = 'Default Admin'
    admin_password = 'your_very_strong_password' # Change this!

    if not User.query.filter_by(email=admin_email).first():
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            admin_user = User(email=admin_email, name=admin_name, role=admin_role, is_active=True)
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user '{admin_name}' ({admin_email}) created.")
        else:
            print("Admin role not found. Cannot create admin user.")
    else:
        print(f"Admin user with email '{admin_email}' already exists.")
    exit()
    ```
    Subsequently, new users can be registered by this admin via the API.

## Running Tests (Placeholder)

A `tests/` directory is set up for unit and integration tests. (Test cases and a test runner like Pytest need to be implemented).
To run tests (once implemented):
```bash
# export FLASK_ENV=testing (or set in .env.test)
# pytest
```

---

This README should provide a comprehensive guide for developers to get started with the project, including local setup and Docker deployment.
""