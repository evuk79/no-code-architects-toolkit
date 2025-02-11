import os
import logging
from abc import ABC, abstractmethod
from typing import Optional
from config import validate_env_vars

logger = logging.getLogger(__name__)

class CloudStorageProvider(ABC):
    """Abstract base class for cloud storage providers."""
    
    @abstractmethod
    def upload_file(self, file_path: str) -> str:
        """Upload a file to cloud storage.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            URL or path to the uploaded file
        """
        pass

class LocalStorageProvider(CloudStorageProvider):
    """Local storage implementation for development/testing."""
    
    def __init__(self):
        self.storage_path = os.getenv('LOCAL_STORAGE_PATH', '/var/www/uploads')
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Initialized local storage at {self.storage_path}")

    def upload_file(self, file_path: str) -> str:
        """Store a file locally.
        
        Args:
            file_path: Path to the file to store
            
        Returns:
            URL/path to the stored file
            
        Raises:
            OSError: If file operation fails
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            filename = os.path.basename(file_path)
            destination = os.path.join(self.storage_path, filename)
            
            os.rename(file_path, destination)
            logger.info(f"File stored successfully: {destination}")
            
            return f"/uploads/{filename}"
        except Exception as e:
            logger.error(f"Error storing file {file_path}: {str(e)}")
            raise

def get_storage_provider() -> CloudStorageProvider:
    """Get the configured storage provider.
    
    Returns:
        Instance of CloudStorageProvider
        
    Raises:
        ValueError: If no valid storage provider is configured
    """
    provider = LocalStorageProvider()
    logger.info("Using local storage provider")
    return provider

def upload_file(file_path: str) -> str:
    """Upload a file using the configured storage provider.
    
    Args:
        file_path: Path to the file to upload
        
    Returns:
        URL or path to the uploaded file
        
    Raises:
        Exception: If upload fails
    """
    provider = get_storage_provider()
    try:
        logger.info(f"Uploading file: {file_path}")
        url = provider.upload_file(file_path)
        logger.info(f"File uploaded successfully: {url}")
        return url
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise