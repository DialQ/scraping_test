# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium with all system dependencies
# The --with-deps flag handles apt-get update and installs all required libs
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
