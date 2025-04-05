# Homelab Media Processing System

This project provides a set of Docker containers for media processing and sharing:

- **MeTube**: YouTube downloader with web interface
- **VideoTranscoder**: Automatically transcodes webm videos to mp4 and creates transcripts
- **NAS**: Samba file sharing server (optional)
- **OpenWebUI**: Web interface for Ollama
- **InfluxDB & Grafana**: Monitoring and visualization

## System Requirements

- Docker and Docker Compose
- FFmpeg (installed in the container)
- For Mac/Desktop: Local Ollama installation (optional)
- For Raspberry Pi: No additional requirements (Ollama runs in container)

## Setup and Deployment

### On Mac/Desktop

#### Option 1: Standard Deployment (No NAS, using Docker volumes)

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

#### Option 2: Local Folder Deployment (No NAS, using local folder)

This option stores transcriptions in a local folder on your Mac:

1. Install and start Ollama as above

2. Deploy with local folder:

   ```
   make deploy-mac-local
   ```

   This will create a folder at `~/Downloads/transcriptions` and use it for storage.

#### Option 3: With NAS Service

If you want to use the Samba NAS service on Mac:

```
make deploy-with-nas
```

### On Raspberry Pi

Deploy the stack with Ollama in container and NAS service:

```
make deploy-pi
```

## Usage

### VideoTranscoder

The VideoTranscoder service monitors the shared downloads directory. When a `.webm` file is detected:

1. It creates a new folder with the name of the video
2. Converts the webm to mp4
3. Generates a transcript of the audio with the naming format `TITLE - MM/DD/YYYY.txt`
4. Deletes the original webm file

The final structure will be:

```
/share/
  video_title/
    video_title.mp4
    video_title - MM/DD/YYYY.txt
```

### Accessing Files

#### When using local folder (Option 2):

Files are stored directly in `~/Downloads/transcriptions` on your Mac.

#### When using Docker volumes (Option 1) or NAS (Option 3):

- Through Samba (Option 3 only): `smb://localhost/Downloads`
- Through Docker commands:
  ```
  docker run --rm -v homelab_shared_downloads:/source -v $(pwd):/destination alpine cp -r /source /destination
  ```

### Accessing Services

- MeTube: http://localhost:8081
- VideoTranscoder API: http://localhost:5001
- Samba Share (if using NAS): Available at `\\localhost\Downloads` on Windows or `smb://localhost/Downloads` on Mac
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
