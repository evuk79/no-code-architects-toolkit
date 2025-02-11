from flask import request, jsonify, current_app
from functools import wraps
import jsonschema
import logging
from typing import Callable, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_payload(schema: Dict[str, Any]) -> Callable:
    """
    Decorator to validate JSON payload against a schema.
    
    Args:
        schema (Dict[str, Any]): JSON schema to validate against
        
    Returns:
        Callable: Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.json:
                logger.warning("Missing JSON in request")
                return jsonify({"message": "Missing JSON in request"}), 400
            
            try:
                jsonschema.validate(instance=request.json, schema=schema)
            except jsonschema.exceptions.ValidationError as validation_error:
                logger.error(f"Invalid payload: {validation_error.message}")
                return jsonify({
                    "message": f"Invalid payload: {validation_error.message}"
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def queue_task_wrapper(bypass_queue: bool = False) -> Callable:
    """
    Decorator to wrap functions with queue task functionality.
    
    Args:
        bypass_queue (bool): Whether to bypass the queue
        
    Returns:
        Callable: Decorated function
    """
    def decorator(f: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            return current_app.queue_task(bypass_queue=bypass_queue)(f)(*args, **kwargs)
        return wrapper
    return decorator

def validate_headers(required_headers: list) -> Callable:
    """
    Decorator to validate required headers in the request.
    
    Args:
        required_headers (list): List of required headers
        
    Returns:
        Callable: Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            missing_headers = [header for header in required_headers if header not in request.headers]
            if missing_headers:
                logger.warning(f"Missing required headers: {', '.join(missing_headers)}")
                return jsonify({
                    "message": f"Missing required headers: {', '.join(missing_headers)}"
                }), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator

def handle_errors(f: Callable) -> Callable:
    """
    Decorator to handle unexpected errors in route handlers.
    
    Args:
        f (Callable): Function to wrap
        
    Returns:
        Callable: Decorated function
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({"message": "An unexpected error occurred"}), 500
    return wrapper