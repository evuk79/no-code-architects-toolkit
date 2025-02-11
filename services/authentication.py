from functools import wraps
from flask import request, jsonify
from typing import Callable, Any
import logging
from config import API_KEY

logger = logging.getLogger(__name__)

def authenticate(func: Callable) -> Callable:
    """Decorator to authenticate API requests using API key.
    
    Args:
        func: The route function to protect
        
    Returns:
        Wrapped function that checks authentication
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function that performs authentication."""
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Missing API key in request")
            return jsonify({
                "message": "Unauthorized",
                "error": "API key is required"
            }), 401
            
        if api_key != API_KEY:
            logger.warning(f"Invalid API key provided: {api_key}")
            return jsonify({
                "message": "Unauthorized", 
                "error": "Invalid API key"
            }), 401
            
        logger.info("Request authenticated successfully")
        return func(*args, **kwargs)
        
    return wrapper
