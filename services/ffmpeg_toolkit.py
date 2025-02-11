import os
import ffmpeg
import logging
from typing import List, Dict, Optional
from services.file_management import download_file

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

STORAGE_PATH = "/tmp/"

class FFmpegProcessor:
    """Class to handle FFmpeg processing operations."""
    
    def __init__(self):
        self.storage_path = STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Initialized FFmpeg processor with storage path: {self.storage_path}")

    def convert_media(
        self,
        media_url: str,
        job_id: str,
        bitrate: str = '128k',
        webhook_url: Optional[str] = None
    ) -> str:
        """Convert media file to MP3 format.
        
        Args:
            media_url: URL of media file to convert
            job_id: Unique job identifier
            bitrate: Audio bitrate for conversion
            webhook_url: Optional webhook URL for notifications
            
        Returns:
            Path to converted file
            
        Raises:
            Exception: If conversion fails
        """
        try:
            # Download media file
            input_filename = download_file(
                media_url,
                os.path.join(self.storage_path, f"{job_id}_input")
            )
            logger.info(f"Job {job_id}: Media downloaded to {input_filename}")
            
            # Set output path
            output_filename = f"{job_id}.mp3"
            output_path = os.path.join(self.storage_path, output_filename)
            
            # Convert media
            logger.info(f"Job {job_id}: Converting media to MP3 with bitrate {bitrate}")
            (
                ffmpeg
                .input(input_filename)
                .output(output_path, acodec='libmp3lame', audio_bitrate=bitrate)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Clean up input file
            self._cleanup_file(input_filename)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Job {job_id}: Media conversion failed - {str(e)}")
            raise

    def combine_videos(
        self,
        media_urls: List[Dict[str, str]],
        job_id: str,
        webhook_url: Optional[str] = None
    ) -> str:
        """Combine multiple videos into one.
        
        Args:
            media_urls: List of video URLs to combine
            job_id: Unique job identifier
            webhook_url: Optional webhook URL for notifications
            
        Returns:
            Path to combined video file
            
        Raises:
            Exception: If combination fails
        """
        try:
            # Download all media files
            input_files = []
            for i, media_item in enumerate(media_urls):
                url = media_item['video_url']
                input_filename = download_file(
                    url,
                    os.path.join(self.storage_path, f"{job_id}_input_{i}")
                )
                input_files.append(input_filename)
                logger.info(f"Job {job_id}: Downloaded video {i+1} to {input_filename}")
            
            # Generate concat list file
            concat_file_path = os.path.join(self.storage_path, f"{job_id}_concat_list.txt")
            with open(concat_file_path, 'w') as concat_file:
                for input_file in input_files:
                    concat_file.write(f"file '{os.path.abspath(input_file)}'\n")
            
            # Set output path
            output_filename = f"{job_id}.mp4"
            output_path = os.path.join(self.storage_path, output_filename)
            
            # Combine videos
            logger.info(f"Job {job_id}: Combining videos")
            (
                ffmpeg.input(concat_file_path, format='concat', safe=0)
                .output(output_path, c='copy')
                .run(overwrite_output=True)
            )
            
            # Clean up temporary files
            for f in input_files:
                self._cleanup_file(f)
            self._cleanup_file(concat_file_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Job {job_id}: Video combination failed - {str(e)}")
            raise

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

def process_conversion(
    media_url: str,
    job_id: str,
    bitrate: str = '128k',
    webhook_url: Optional[str] = None
) -> str:
    """Public interface for media conversion."""
    processor = FFmpegProcessor()
    return processor.convert_media(media_url, job_id, bitrate, webhook_url)

def process_video_combination(
    media_urls: List[Dict[str, str]],
    job_id: str,
    webhook_url: Optional[str] = None
) -> str:
    """Public interface for video combination."""
    processor = FFmpegProcessor()
    return processor.combine_videos(media_urls, job_id, webhook_url)
