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
    pkg-config \
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
ENV FLASK_APP "main:create_app()" # <-- Updated here
ENV PATH=$APP_HOME/.local/bin:$PATH

WORKDIR $APP_HOME

# Create a non-root user and group
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup -d $APP_HOME appuser

# Install only necessary OS-level runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code from the builder stage
COPY --from=builder $APP_HOME $APP_HOME

# Change ownership of the app directory to the appuser
RUN chown -R appuser:appgroup $APP_HOME

# Grant necessary permissions explicitly:
# For directories: owner (appuser) gets rwx, group & others get rx (755 equivalent for owner)
# For files: owner (appuser) gets rw, group & others get r (644 equivalent for owner)
RUN find $APP_HOME -type d -exec chmod u=rwx,go=rx {} + && \
    find $APP_HOME -type f -exec chmod u=rw,go=r {} +

# Switch to the non-root user
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--log-level", "info", "main:create_app()"] # <-- Updated here