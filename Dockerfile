# Dockerfile (Refined)

# Stage 1: Builder - To install dependencies and build artifacts
FROM python:3.9-slim-buster AS builder

ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

WORKDIR $APP_HOME

# Install OS-level dependencies for mysqlclient and other build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code last in builder stage after dependencies are installed
COPY . .

# Stage 2: Runtime - Smaller final image with only necessary artifacts
FROM python:3.9-slim-buster AS runtime

ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
ENV FLASK_ENV production
ENV FLASK_APP "app:create_app()"
ENV PATH=$APP_HOME/.local/bin:$PATH

WORKDIR $APP_HOME

# Create a non-root user and group
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup -d $APP_HOME appuser

# Install only necessary OS-level runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
# Ensure these paths are correct based on how pip installs them in the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code from the builder stage
COPY --from=builder $APP_HOME $APP_HOME

# Change ownership of the app directory to the appuser
RUN chown -R appuser:appgroup $APP_HOME

# Switch to the non-root user
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--log-level", "info", "app:create_app()"]