import os
import subprocess
import logging
from typing import Optional
from PIL import Image
from services.file_management import download_file

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

STORAGE_PATH = "/tmp/"

class ImageToVideoConverter:
    """Class to handle image to video conversion."""
    
    def __init__(self):
        self.storage_path = STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Initialized image to video converter with storage path: {self.storage_path}")

    def convert_image_to_video(
        self,
        image_url: str,
        length: float,
        frame_rate: float,
        zoom_speed: float,
        job_id: str,
        webhook_url: Optional[str] = None
    ) -> str:
        """Convert an image to a video with zoom effect.
        
        Args:
            image_url: URL of the image to convert
            length: Length of output video in seconds
            frame_rate: Frame rate of output video
            zoom_speed: Zoom speed factor
            job_id: Unique job identifier
            webhook_url: Optional webhook URL for notifications
            
        Returns:
            Path to converted video file
            
        Raises:
            subprocess.CalledProcessError: If FFmpeg command fails
            Exception: For other errors
        """
        try:
            # Download image file
            image_path = download_file(image_url, self.storage_path)
            logger.info(f"Job {job_id}: Image downloaded to {image_path}")
            
            # Get image dimensions
            with Image.open(image_path) as img:
                width, height = img.size
            logger.info(f"Job {job_id}: Image dimensions: {width}x{height}")
            
            # Determine video dimensions based on orientation
            scale_dims, output_dims = self._get_video_dimensions(width, height)
            
            # Calculate video parameters
            total_frames = int(length * frame_rate)
            zoom_factor = 1 + (zoom_speed * length)
            
            logger.info(f"Job {job_id}: Video parameters - "
                       f"Length: {length}s, Frame rate: {frame_rate}fps, "
                       f"Total frames: {total_frames}, Zoom factor: {zoom_factor}")
            
            # Set output path
            output_path = os.path.join(self.storage_path, f"{job_id}.mp4")
            
            # Prepare FFmpeg command
            cmd = [
                'ffmpeg', '-framerate', str(frame_rate), '-loop', '1', '-i', image_path,
                '-vf', f"scale={scale_dims},zoompan=z='min(1+({zoom_speed}*{length})*on/{total_frames}, {zoom_factor})':"
                      f"d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={output_dims}",
                '-c:v', 'libx264', '-t', str(length), '-pix_fmt', 'yuv420p', output_path
            ]
            
            logger.info(f"Job {job_id}: Running FFmpeg command: {' '.join(cmd)}")
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr)
            
            # Clean up image file
            self._cleanup_file(image_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Job {job_id}: Image to video conversion failed - {str(e)}")
            raise

    def _get_video_dimensions(self, width: int, height: int) -> tuple[str, str]:
        """Determine video dimensions based on image orientation.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            Tuple of (scale dimensions, output dimensions)
        """
        if width > height:  # Landscape
            return "7680:4320", "1920x1080"
        else:  # Portrait
            return "4320:7680", "1080x1920"

    def _cleanup_file(self, file_path: str) -> None:
        """Clean up a file.
        
        Args:
            file_path: Path to file to remove
            
        Raises:
            OSError: If file removal fails
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except OSError as e:
            logger.warning(f"Error removing file {file_path}: {str(e)}")
            raise

def process_image_to_video(
    image_url: str,
    length: float,
    frame_rate: float,
    zoom_speed: float,
    job_id: str,
    webhook_url: Optional[str] = None
) -> str:
    """Public interface for image to video conversion."""
    converter = ImageToVideoConverter()
    return converter.convert_image_to_video(
        image_url, length, frame_rate, zoom_speed, job_id, webhook_url)