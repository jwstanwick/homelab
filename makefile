.PHONY: deploy deploy-mac deploy-pi down

# Default deployment (for Mac/desktop)
deploy:
	OLLAMA_API_URL=http://localhost:11434/api docker compose up -d

# Specific deployment for Mac/desktop (uses local Ollama)
deploy-mac:
	OLLAMA_API_URL=http://localhost:11434/api docker compose up -d

# Deployment for Raspberry Pi (uses containerized Ollama)
deploy-pi:
	docker compose --profile raspberry_pi up -d

# Stop all containers
down:
	docker compose down

# Rebuild and deploy (for development)
rebuild:
	docker compose build --no-cache videotranscoder
	make deploy