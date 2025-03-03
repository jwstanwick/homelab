# Homelab Media Processing System

This project provides a set of Docker containers for media processing and sharing:

- **MeTube**: YouTube downloader with web interface
- **VideoTranscoder**: Automatically transcodes webm videos to mp4 and creates transcripts
- **NAS**: Samba file sharing server
- **OpenWebUI**: Web interface for Ollama
- **InfluxDB & Grafana**: Monitoring and visualization

## System Requirements

- Docker and Docker Compose
- FFmpeg (installed in the container)
- For Mac/Desktop: Local Ollama installation (optional)
- For Raspberry Pi: No additional requirements (Ollama runs in container)

## Setup and Deployment

### On Mac/Desktop

1. Install Ollama locally if you want to use AI features:

   ```
   brew install ollama
   ```

2. Start Ollama locally:

   ```
   ollama serve
   ```

3. Deploy the stack:
   ```
   make deploy
   ```

### On Raspberry Pi

1. Deploy the stack with Ollama in container:
   ```
   make deploy-pi
   ```

## Usage

### VideoTranscoder

The VideoTranscoder service monitors the shared downloads directory. When a `.webm` file is detected:

1. It creates a new folder with the name of the video
2. Converts the webm to mp4
3. Generates a transcript of the audio
4. Deletes the original webm file

### Accessing Services

- MeTube: http://localhost:8081
- VideoTranscoder API: http://localhost:5001
- Samba Share: Available at `\\localhost\Downloads` on Windows or `smb://localhost/Downloads` on Mac
- OpenWebUI: http://localhost:3002
- InfluxDB: http://localhost:8086
- Grafana: http://localhost:3003

## Troubleshooting

If you encounter port conflicts, edit the `docker-compose.yml` file to change the port mappings.

To check the logs of a specific service:

```
docker logs <container_name>
```

For example:

```
docker logs videotranscoder
```
