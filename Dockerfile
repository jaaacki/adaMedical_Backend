FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install MySQL client for command line operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-mysql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Simple command using Flask development server
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]