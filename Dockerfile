# Use Node.js for the frontend
FROM node:18-alpine as frontend

WORKDIR /app/web
COPY web/package*.json ./
RUN npm install
COPY web/ .
RUN npm run build

# Use Python for the backend
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y build-essential swig libpcsclite-dev pcscd && \
    apt-get install -y --only-upgrade libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Copy backend code
COPY *.py ./

# Copy frontend build
COPY --from=frontend /app/web/build ./web/build

# Expose ports
EXPOSE 5000

# Start the Flask application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "web_server:app"] 