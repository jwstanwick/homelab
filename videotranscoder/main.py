import os
import time
from flask import Flask, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ffmpeg
import whisper
import threading
import logging
from pathlib import Path
import sys

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize the Whisper model
try:
    logger.info("Loading Whisper model...")
    model = whisper.load_model("base")
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {str(e)}")
    sys.exit(1)

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.webm':
            logger.info(f"New webm file detected: {file_path}")
            # Process in a separate thread to not block the observer
            threading.Thread(target=self.process_video, args=(file_path,)).start()

    def process_video(self, webm_path):
        try:
            logger.info(f"Starting to process {webm_path}")
            
            # Create output directory with video name
            output_dir = webm_path.parent / webm_path.stem
            output_dir.mkdir(exist_ok=True)
            
            # Output paths
            mp4_path = output_dir / f"{webm_path.stem}.mp4"
            transcript_path = output_dir / "transcript.txt"

            # Convert webm to mp4
            logger.info(f"Converting {webm_path} to MP4")
            try:
                stream = ffmpeg.input(str(webm_path))
                stream = ffmpeg.output(stream, str(mp4_path))
                ffmpeg.run(stream, overwrite_output=True)
                logger.info(f"Conversion to MP4 completed: {mp4_path}")
            except Exception as e:
                logger.error(f"FFmpeg conversion failed: {str(e)}")
                raise

            # Generate transcript
            logger.info(f"Generating transcript for {mp4_path}")
            try:
                result = model.transcribe(str(mp4_path))
                logger.info("Transcription completed")
            except Exception as e:
                logger.error(f"Transcription failed: {str(e)}")
                raise

            # Save transcript
            try:
                with open(transcript_path, 'w') as f:
                    f.write(result["text"])
                logger.info(f"Transcript saved to {transcript_path}")
            except Exception as e:
                logger.error(f"Failed to save transcript: {str(e)}")
                raise

            # Delete original webm file
            try:
                os.remove(webm_path)
                logger.info(f"Original webm file deleted: {webm_path}")
            except Exception as e:
                logger.error(f"Failed to delete original webm file: {str(e)}")
                # Continue even if deletion fails

            logger.info(f"Successfully processed {webm_path}")

        except Exception as e:
            logger.error(f"Error processing {webm_path}: {str(e)}")

class FileMonitor:
    def __init__(self, path_to_watch):
        self.path_to_watch = path_to_watch
        self.observer = Observer()
        self.running = False

    def start(self):
        if not os.path.exists(self.path_to_watch):
            logger.error(f"Watch path does not exist: {self.path_to_watch}")
            logger.info("Creating watch path directory")
            try:
                os.makedirs(self.path_to_watch, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create watch path: {str(e)}")
                return False

        event_handler = VideoHandler()
        self.observer.schedule(event_handler, self.path_to_watch, recursive=False)
        self.observer.start()
        self.running = True
        logger.info(f"Started monitoring {self.path_to_watch}")
        return True

    def stop(self):
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("File monitoring stopped")

# Initialize file monitor
WATCH_PATH = "/share"  # This matches the path in the container
monitor = FileMonitor(WATCH_PATH)

@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "monitoring_path": WATCH_PATH,
        "monitoring_active": monitor.running
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy"
    }), 200

def start_monitoring():
    success = monitor.start()
    if not success:
        logger.error("Failed to start file monitoring")
        # Continue running the Flask server even if monitoring fails

if __name__ == '__main__':
    # Start the file monitor in a separate thread
    monitoring_thread = threading.Thread(target=start_monitoring)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    # Start Flask server
    logger.info("Starting Flask server on port 5000")
    app.run(host='0.0.0.0', port=5000)
