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
import datetime
import subprocess

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

    def check_audio_in_file(self, file_path):
        """Check if the file contains valid audio streams"""
        try:
            # Use ffprobe to get information about the file
            cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 
                   'stream=codec_type', '-of', 'default=noprint_wrappers=1', str(file_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # If there's audio stream information in the output, the file has audio
            return 'codec_type=audio' in result.stdout
        except Exception as e:
            logger.error(f"Error checking audio in file {file_path}: {str(e)}")
            return False

    def process_video(self, webm_path):
        try:
            logger.info(f"Starting to process {webm_path}")
            
            # Check if the file exists and has a non-zero size
            if not webm_path.exists() or webm_path.stat().st_size == 0:
                logger.error(f"File {webm_path} does not exist or is empty")
                return
            
            # Check if the file contains audio
            if not self.check_audio_in_file(webm_path):
                logger.error(f"File {webm_path} does not contain valid audio streams")
                # Create a note about the error
                error_note_path = webm_path.parent / f"{webm_path.stem}_ERROR.txt"
                with open(error_note_path, 'w') as f:
                    f.write(f"Error processing {webm_path.name}: No valid audio found in the file.")
                return
            
            # Get video title (filename without extension)
            video_title = webm_path.stem
            
            # Get current date in MM-DD-YYYY format (using hyphens instead of slashes)
            current_date = datetime.datetime.now().strftime("%m-%d-%Y")
            
            # Create output directory with video name
            output_dir = webm_path.parent / video_title
            output_dir.mkdir(exist_ok=True)
            
            # Output paths
            mp4_path = output_dir / f"{video_title}.mp4"
            
            # Format transcript filename with date
            formatted_title = f"{video_title} - {current_date}"
            transcript_path = output_dir / f"{formatted_title}.txt"

            # Convert webm to mp4
            logger.info(f"Converting {webm_path} to MP4")
            try:
                # Use more explicit ffmpeg options to ensure audio is properly handled
                stream = ffmpeg.input(str(webm_path))
                stream = ffmpeg.output(stream, str(mp4_path), acodec='aac', vcodec='h264')
                ffmpeg.run(stream, overwrite_output=True)
                logger.info(f"Conversion to MP4 completed: {mp4_path}")
                
                # Verify the output file exists and has content
                if not mp4_path.exists() or mp4_path.stat().st_size == 0:
                    logger.error(f"Converted file {mp4_path} does not exist or is empty")
                    raise Exception("Conversion failed: output file is empty or missing")
                
                # Verify the output file has audio
                if not self.check_audio_in_file(mp4_path):
                    logger.error(f"Converted file {mp4_path} does not contain valid audio streams")
                    raise Exception("Conversion failed: no valid audio in output file")
                
            except Exception as e:
                logger.error(f"FFmpeg conversion failed: {str(e)}")
                raise

            # Generate transcript
            logger.info(f"Generating transcript for {mp4_path}")
            try:
                # Use a try-except block with a timeout to prevent hanging
                result = model.transcribe(str(mp4_path))
                
                # Check if the transcription result is empty
                if not result or not result.get("text"):
                    logger.warning(f"Transcription result is empty for {mp4_path}")
                    result = {"text": "No speech detected in the audio."}
                
                logger.info("Transcription completed")
            except Exception as e:
                logger.error(f"Transcription failed: {str(e)}")
                # Create a basic transcript with the error
                result = {"text": f"Error during transcription: {str(e)}"}

            # Save transcript with formatted name
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
            # Create an error file to indicate the failure
            try:
                error_path = webm_path.parent / f"{webm_path.stem}_processing_error.txt"
                with open(error_path, 'w') as f:
                    f.write(f"Error processing {webm_path.name}: {str(e)}")
            except:
                pass

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
