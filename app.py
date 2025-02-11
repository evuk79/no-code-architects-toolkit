from flask import Flask, request
from queue import Queue
from services.webhook import send_webhook
import threading
import uuid
import os
import time
import logging
from version import BUILD_NUMBER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_QUEUE_LENGTH = int(os.environ.get('MAX_QUEUE_LENGTH', 0))

class TaskQueueManager:
    """Manages task queue and processing."""
    
    def __init__(self):
        self.task_queue = Queue()
        self.queue_id = id(self.task_queue)
        self._start_processing_thread()

    def _start_processing_thread(self):
        """Start the queue processing thread."""
        threading.Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self):
        """Process tasks from the queue."""
        while True:
            try:
                job_id, data, task_func, queue_start_time = self.task_queue.get()
                queue_time = time.time() - queue_start_time
                run_start_time = time.time()
                pid = os.getpid()
                
                response = task_func()
                run_time = time.time() - run_start_time
                total_time = time.time() - queue_start_time

                response_data = {
                    "endpoint": response[1],
                    "code": response[2],
                    "id": data.get("id"),
                    "job_id": job_id,
                    "response": response[0] if response[2] == 200 else None,
                    "message": "success" if response[2] == 200 else response[0],
                    "pid": pid,
                    "queue_id": self.queue_id,
                    "run_time": round(run_time, 3),
                    "queue_time": round(queue_time, 3),
                    "total_time": round(total_time, 3),
                    "queue_length": self.task_queue.qsize(),
                    "build_number": BUILD_NUMBER
                }

                send_webhook(data.get("webhook_url"), response_data)
                self.task_queue.task_done()

            except Exception as e:
                logger.error(f"Error processing task: {str(e)}")
                continue

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    task_manager = TaskQueueManager()

    def queue_task(bypass_queue=False):
        """Decorator to add tasks to the queue or bypass it."""
        def decorator(f):
            def wrapper(*args, **kwargs):
                job_id = str(uuid.uuid4())
                data = request.json if request.is_json else {}
                pid = os.getpid()
                start_time = time.time()
                
                if bypass_queue or 'webhook_url' not in data:
                    response = f(job_id=job_id, data=data, *args, **kwargs)
                    run_time = time.time() - start_time
                    return {
                        "code": response[2],
                        "id": data.get("id"),
                        "job_id": job_id,
                        "response": response[0] if response[2] == 200 else None,
                        "message": "success" if response[2] == 200 else response[0],
                        "run_time": round(run_time, 3),
                        "queue_time": 0,
                        "total_time": round(run_time, 3),
                        "pid": pid,
                        "queue_id": task_manager.queue_id,
                        "queue_length": task_manager.task_queue.qsize(),
                        "build_number": BUILD_NUMBER
                    }, response[2]
                else:
                    if MAX_QUEUE_LENGTH > 0 and task_manager.task_queue.qsize() >= MAX_QUEUE_LENGTH:
                        return {
                            "code": 429,
                            "id": data.get("id"),
                            "job_id": job_id,
                            "message": f"MAX_QUEUE_LENGTH ({MAX_QUEUE_LENGTH}) reached",
                            "pid": pid,
                            "queue_id": task_manager.queue_id,
                            "queue_length": task_manager.task_queue.qsize(),
                            "build_number": BUILD_NUMBER
                        }, 429
                    
                    task_manager.task_queue.put((job_id, data, lambda: f(job_id=job_id, data=data, *args, **kwargs), start_time))
                    
                    return {
                        "code": 202,
                        "id": data.get("id"),
                        "job_id": job_id,
                        "message": "processing",
                        "pid": pid,
                        "queue_id": task_manager.queue_id,
                        "max_queue_length": MAX_QUEUE_LENGTH if MAX_QUEUE_LENGTH > 0 else "unlimited",
                        "queue_length": task_manager.task_queue.qsize(),
                        "build_number": BUILD_NUMBER
                    }, 202
            return wrapper
        return decorator

    app.queue_task = queue_task

    # Import and register blueprints
    from routes.media_to_mp3 import convert_bp
    from routes.transcribe_media import transcribe_bp
    from routes.combine_videos import combine_bp
    from routes.audio_mixing import audio_mixing_bp
    from routes.gdrive_upload import gdrive_upload_bp
    from routes.authenticate import auth_bp
    from routes.caption_video import caption_bp
    from routes.extract_keyframes import extract_keyframes_bp
    from routes.image_to_video import image_to_video_bp
    
    app.register_blueprint(convert_bp)
    app.register_blueprint(transcribe_bp)
    app.register_blueprint(combine_bp)
    app.register_blueprint(audio_mixing_bp)
    app.register_blueprint(gdrive_upload_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(caption_bp)
    app.register_blueprint(extract_keyframes_bp)
    app.register_blueprint(image_to_video_bp)

    # Version 1.0 blueprints
    from routes.v1.ffmpeg.ffmpeg_compose import v1_ffmpeg_compose_bp
    from routes.v1.media.media_transcribe import v1_media_transcribe_bp
    from routes.v1.media.transform.media_to_mp3 import v1_media_transform_mp3_bp
    from routes.v1.video.concatenate import v1_video_concatenate_bp
    from routes.v1.video.caption_video import v1_video_caption_bp
    from routes.v1.image.transform.image_to_video import v1_image_transform_video_bp
    from routes.v1.toolkit.test import v1_toolkit_test_bp
    from routes.v1.toolkit.authenticate import v1_toolkit_auth_bp
    from routes.v1.code.execute.execute_python import v1_code_execute_bp

    app.register_blueprint(v1_ffmpeg_compose_bp)
    app.register_blueprint(v1_media_transcribe_bp)
    app.register_blueprint(v1_media_transform_mp3_bp)
    app.register_blueprint(v1_video_concatenate_bp)
    app.register_blueprint(v1_video_caption_bp)
    app.register_blueprint(v1_image_transform_video_bp)
    app.register_blueprint(v1_toolkit_test_bp)
    app.register_blueprint(v1_toolkit_auth_bp)
    app.register_blueprint(v1_code_execute_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)