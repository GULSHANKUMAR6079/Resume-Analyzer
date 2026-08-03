# Multi-stage Dockerfile for Render Backend Deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for WeasyPrint, OpenCV/Pango, and C compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpango-1.0-0 \
    harfbuzz-bin \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    ffi-dev \
    shared-mime-info \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_md

# Copy application source code
COPY . .

# Expose port (Render overrides PORT via environment variable)
EXPOSE 8000

# Start FastAPI backend
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
