# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright and Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN playwright install chromium --with-deps

# Copy the rest of the application code
COPY . .

# Set environment variables
# Cloud Run sets the PORT environment variable
ENV PORT=9500
ENV HOST=0.0.0.0

# Expose the port (Cloud Run ignores this but it's good practice)
EXPOSE 9500

# Command to run the application
# We use uvicorn directly to ensure it picks up the PORT env var correctly
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
