.PHONY: deploy deploy-mac deploy-mac-local deploy-pi deploy-with-nas down

# Default deployment (for Mac/desktop with local Ollama, no NAS)
deploy:
	OLLAMA_API_URL=http://localhost:11434/api docker-compose up -d

# Specific deployment for Mac/desktop (uses local Ollama, no NAS)
deploy-mac:
	OLLAMA_API_URL=http://localhost:11434/api docker-compose up -d

# Deployment for Mac with local folder for downloads
deploy-mac-local:
	mkdir -p ~/Downloads/transcriptions
	LOCAL_DOWNLOADS_PATH=~/Downloads/transcriptions OLLAMA_API_URL=http://localhost:11434/api docker-compose up -d

# Deployment for Mac with NAS service
deploy-with-nas:
	OLLAMA_API_URL=http://localhost:11434/api docker-compose --profile with_nas up -d

# Deployment for Raspberry Pi (uses containerized Ollama and NAS)
deploy-pi:
	docker-compose --profile raspberry_pi --profile with_nas up -d

# Stop all containers
down:
	docker-compose down

ssh:
	ssh 10.0.0.173
	
# Rebuild and deploy (for development)
rebuild:
	docker-compose build --no-cache videotranscoder
	make deploy