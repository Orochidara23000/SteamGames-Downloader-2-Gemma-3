FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (including those for SteamCMD)
RUN apt-get update && apt-get install -y \
    lib32gcc-s1 \
    wget \
    tar \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY *.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create required directories
RUN mkdir -p /data/logs /data/downloads /app/steamcmd

# Environment variables
ENV PORT=8000
ENV API_PORT=8000
ENV ENABLE_GRADIO=True
ENV PERSISTENT_DIR="/data"

# Make the script executable
RUN chmod +x /app/main.py

# Expose ports
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"] 