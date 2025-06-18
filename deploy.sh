#!/bin/bash

# Build and start the containers
docker-compose up -d --build

# Wait for the application to start
echo "Waiting for the application to start..."
sleep 10

# Initialize the database
docker-compose exec app python init_corporate_db.py

echo "Deployment complete! The application is running at http://localhost:5000" 