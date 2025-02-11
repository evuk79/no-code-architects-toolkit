import os
import logging
from abc import ABC, abstractmethod
from config import validate_env_vars

logger = logging.getLogger(__name__)

class CloudStorageProvider(ABC):
    @abstractmethod
    def upload_file(self, file_path: str) -> str:
        pass

class LocalStorageProvider(CloudStorageProvider):
    def __init__(self):
        self.storage_path = os.getenv('LOCAL_STORAGE_PATH', '/var/www/uploads')
        os.makedirs(self.storage_path, exist_ok=True)

    def upload_file(self, file_path: str) -> str:
        try:
            filename = os.path.basename(file_path)
            destination = os.path.join(self.storage_path, filename)
            
            # Move the file to the storage location
            os.rename(file_path, destination)
            
            # Return the URL/path to the stored file
            return f"/uploads/{filename}"
        except Exception as e:
            logger.error(f"Error storing file locally: {e}")
            raise

def get_storage_provider() -> CloudStorageProvider:
    return LocalStorageProvider()

def upload_file(file_path: str) -> str:
    provider = get_storage_provider()
    try:
        logger.info(f"Storing file locally: {file_path}")
        url = provider.upload_file(file_path)
        logger.info(f"File stored successfully: {url}")
        return url
    except Exception as e:
        logger.error(f"Error storing file: {e}")
        raise