# Dockerfile for Triple-Shield Architecture (3SA)
# Base image: Ubuntu 22.04 LTS with Python 3.13
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/app/.local/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    iproute2 \
    cmake \
    ninja-build \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Note: liboqs Python bindings require complex build process
# For development/testing, we use the mock implementation in oqs_middleware.py
# The mock uses exact byte sizes from literature and is sufficient for AI training


# Create application user
RUN useradd -m -u 1000 app

# Set working directory
WORKDIR /home/app/3sa

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R app:app /home/app/3sa

# Switch to app user
USER app

# Default command: run 3SA with ML-KEM-768
CMD ["python3", "3SA.py", "--kem", "ML-KEM-768"]
