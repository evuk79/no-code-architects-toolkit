import requests
import logging
from typing import Any, Optional

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class WebhookManager:
    """Class to handle webhook operations."""
    
    def __init__(self):
        self.timeout = 10  # seconds
        logger.info("Initialized webhook manager")

    def send_webhook(
        self,
        webhook_url: str,
        data: Any,
        timeout: Optional[int] = None
    ) -> bool:
        """Send a POST request to a webhook URL.
        
        Args:
            webhook_url: URL to send the webhook to
            data: Data to send in the webhook
            timeout: Optional timeout in seconds
            
        Returns:
            True if webhook was sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending webhook to {webhook_url}")
            
            response = requests.post(
                webhook_url,
                json=data,
                timeout=timeout if timeout else self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"Webhook sent successfully to {webhook_url}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook failed for {webhook_url}: {str(e)}")
            return False

def send_webhook(webhook_url: str, data: Any) -> bool:
    """Public interface for sending webhooks."""
    manager = WebhookManager()
    return manager.send_webhook(webhook_url, data)
