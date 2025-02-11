import os
import uuid
import requests
import logging
from typing import Optional
from urllib.parse import urlparse, parse_qs

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FileManager:
    """Class to handle file management operations."""
    
    def __init__(self, storage_path: str = "/tmp/"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Initialized file manager with storage path: {self.storage_path}")

    def download_file(self, url: str, storage_path: Optional[str] = None) -> str:
        """Download a file from a URL.
        
        Args:
            url: URL of the file to download
            storage_path: Optional custom storage path
            
        Returns:
            Path to the downloaded file
            
        Raises:
            requests.RequestException: If download fails
            OSError: If file operations fail
        """
        try:
            # Use provided storage path or default
            target_path = storage_path if storage_path else self.storage_path
            
            # Parse URL and generate filename
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            file_id = str(uuid.uuid4())
            local_filename = os.path.join(target_path, f"{file_id}.mp4")
            
            # Ensure storage directory exists
            os.makedirs(target_path, exist_ok=True)
            
            # Download file
            logger.info(f"Downloading file from {url} to {local_filename}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"File downloaded successfully: {local_filename}")
            return local_filename
            
        except requests.RequestException as e:
            logger.error(f"Download failed for {url}: {str(e)}")
            raise
        except OSError as e:
            logger.error(f"File operation failed: {str(e)}")
            raise

    def delete_old_files(self, max_age_seconds: int = 3600) -> None:
        """Delete old files from storage.
        
        Args:
            max_age_seconds: Maximum age of files to keep (in seconds)
        """
        try:
            now = time.time()
            for filename in os.listdir(self.storage_path):
                file_path = os.path.join(self.storage_path, filename)
                if os.path.isfile(file_path):
                    file_age = now - os.stat(file_path).st_mtime
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            logger.info(f"Deleted old file: {file_path}")
                        except OSError as e:
                            logger.warning(f"Error deleting file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error cleaning old files: {str(e)}")
            raise

def download_file(url: str, storage_path: Optional[str] = None) -> str:
    """Public interface for file download."""
    manager = FileManager()
    return manager.download_file(url, storage_path)

def delete_old_files(max_age_seconds: int = 3600) -> None:
    """Public interface for file cleanup."""
    manager = FileManager()
    manager.delete_old_files(max_age_seconds)
