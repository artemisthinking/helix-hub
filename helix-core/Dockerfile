FROM python:3.11-slim

# System dependencies for paramiko & mt940
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY app.py .
COPY file_processors.py .
COPY dashboard.py .
COPY routing.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Ensure Python output is not buffered
ENV PYTHONUNBUFFERED=1

EXPOSE 5000
CMD ["python", "app.py"]
# helix-core/Dockerfile - Dockerfile for the Helix core application