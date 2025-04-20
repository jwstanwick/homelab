#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Create directory for persistent storage
echo "Creating directory for Ollama models..."
mkdir -p ~/.ollama

# Pull the Ollama Docker image
echo "Pulling Ollama Docker image..."
docker pull ollama/ollama:latest

# Create and start the Ollama container
echo "Creating Ollama container..."
docker run -d \
    --name ollama \
    -p 11434:11434 \
    -v ~/.ollama:/root/.ollama \
    --restart unless-stopped \
    ollama/ollama:latest

# Check if container is running
if docker ps | grep -q ollama; then
    echo "Ollama has been successfully installed and is running!"
    echo "You can access it at http://localhost:11434"
    echo "To pull a model, use: docker exec ollama ollama pull <model-name>"
else
    echo "Failed to start Ollama container. Please check Docker logs."
    docker logs ollama
fi
