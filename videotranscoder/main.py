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

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Whisper model
model = whisper.load_model("base")

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.webm':
            logger.info(f"New webm file detected: {file_path}")
            self.process_video(file_path)

    def process_video(self, webm_path):
        try:
            # Create output directory with video name
            output_dir = webm_path.parent / webm_path.stem
            output_dir.mkdir(exist_ok=True)
            
            # Output paths
            mp4_path = output_dir / f"{webm_path.stem}.mp4"
            transcript_path = output_dir / "transcript.txt"

            # Convert webm to mp4
            logger.info(f"Converting {webm_path} to MP4")
            stream = ffmpeg.input(str(webm_path))
            stream = ffmpeg.output(stream, str(mp4_path))
            ffmpeg.run(stream, overwrite_output=True)

            # Generate transcript
            logger.info(f"Generating transcript for {mp4_path}")
            result = model.transcribe(str(mp4_path))
            
            # Save transcript
            with open(transcript_path, 'w') as f:
                f.write(result["text"])

            # Delete original webm file
            os.remove(webm_path)
            logger.info(f"Successfully processed {webm_path}")

        except Exception as e:
            logger.error(f"Error processing {webm_path}: {str(e)}")

class FileMonitor:
    def __init__(self, path_to_watch):
        self.path_to_watch = path_to_watch
        self.observer = Observer()

    def start(self):
        event_handler = VideoHandler()
        self.observer.schedule(event_handler, self.path_to_watch, recursive=False)
        self.observer.start()
        logger.info(f"Started monitoring {self.path_to_watch}")

    def stop(self):
        self.observer.stop()
        self.observer.join()

# Initialize file monitor
WATCH_PATH = "/share"  # This matches the path in the container
monitor = FileMonitor(WATCH_PATH)

@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "monitoring_path": WATCH_PATH
    })

def start_monitoring():
    monitor.start()

if __name__ == '__main__':
    # Start the file monitor in a separate thread
    monitoring_thread = threading.Thread(target=start_monitoring)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000)
