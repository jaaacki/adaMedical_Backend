FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install only MySQL client for command line operations, not for Python connectivity
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Verify PyMySQL installation
RUN pip show pymysql

# Copy application code
COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--log-level", "debug", "main:create_app"]