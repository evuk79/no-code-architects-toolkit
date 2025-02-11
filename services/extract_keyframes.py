import os
import subprocess
import logging
from typing import List
from services.file_management import download_file

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

STORAGE_PATH = "/tmp/"

class KeyframeExtractor:
    """Class to handle keyframe extraction operations."""
    
    def __init__(self):
        self.storage_path = STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Initialized keyframe extractor with storage path: {self.storage_path}")

    def extract_keyframes(self, video_url: str, job_id: str) -> List[str]:
        """Extract keyframes from a video.
        
        Args:
            video_url: URL of the video to process
            job_id: Unique job identifier
            
        Returns:
            List of paths to extracted keyframes
            
        Raises:
            subprocess.CalledProcessError: If FFmpeg command fails
            Exception: For other errors
        """
        try:
            # Download video file
            video_path = download_file(video_url, self.storage_path)
            logger.info(f"Job {job_id}: Video downloaded to {video_path}")
            
            # Extract keyframes
            output_pattern = os.path.join(self.storage_path, f"{job_id}_%03d.jpg")
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', "select='eq(pict_type,I)',scale=iw*sar:ih,setsar=1",
                '-vsync', 'vfr',
                output_pattern
            ]
            
            logger.info(f"Job {job_id}: Running FFmpeg command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
            # Get extracted keyframes
            keyframes = self._get_keyframe_files(job_id)
            
            # Clean up video file
            self._cleanup_file(video_path)
            
            return keyframes
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Job {job_id}: FFmpeg command failed - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Job {job_id}: Error extracting keyframes - {str(e)}")
            raise

    def _get_keyframe_files(self, job_id: str) -> List[str]:
        """Get list of extracted keyframe files.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            List of paths to keyframe files
        """
        keyframes = []
        for filename in sorted(os.listdir(self.storage_path)):
            if filename.startswith(f"{job_id}_") and filename.endswith(".jpg"):
                file_path = os.path.join(self.storage_path, filename)
                keyframes.append(file_path)
                logger.debug(f"Found keyframe: {file_path}")
        return keyframes

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

def process_keyframe_extraction(video_url: str, job_id: str) -> List[str]:
    """Public interface for keyframe extraction."""
    extractor = KeyframeExtractor()
    return extractor.extract_keyframes(video_url, job_id)