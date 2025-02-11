from flask import Blueprint
from typing import Optional, Tuple, Union, Dict, List
import logging
from services.cloud_storage import upload_file

class BaseRouteHandler:
    """Base class for handling common route operations"""
    
    def __init__(self, name: str):
        self.blueprint = Blueprint(name, __name__)
        self.logger = logging.getLogger(name)
        
    def handle_request(
        self,
        job_id: str,
        data: dict,
        process_func: callable,
        route_path: str
    ) -> Union[Tuple[str, str, int], Tuple[Dict, str, int]]:
        """Handle common request processing flow
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            process_func: Function to process the request
            route_path: Route path for logging
            
        Returns:
            Tuple of (response, route_path, status_code)
            Response can be a string URL or a dictionary
        """
        try:
            # Process the request using the provided function
            result = process_func(job_id, data)
            
            # Handle different response types
            if isinstance(result, str):
                # Single file upload
                cloud_url = upload_file(result)
                self.logger.info(f"Job {job_id}: Processed file uploaded to {cloud_url}")
                return cloud_url, route_path, 200
            elif isinstance(result, dict) and 'image_urls' in result:
                # Multiple file upload (keyframe extraction)
                self.logger.info(f"Job {job_id}: Processed {len(result['image_urls'])} files")
                return result, route_path, 200
            else:
                # Other response types
                self.logger.info(f"Job {job_id}: Processed request with custom response")
                return result, route_path, 200
                
        except Exception as e:
            self.logger.error(f"Job {job_id}: Error processing request - {str(e)}")
            return str(e), route_path, 500
            
    def create_route(
        self,
        path: str,
        methods: list,
        validation_schema: dict,
        process_func: callable
    ):
        """Create a new route with common decorators
        
        Args:
            path: Route path
            methods: HTTP methods
            validation_schema: JSON schema for validation
            process_func: Function to process the request
        """
        @self.blueprint.route(path, methods=methods)
        @authenticate
        @validate_payload(validation_schema)
        @queue_task_wrapper(bypass_queue=False)
        def route_handler(job_id, data):
            return self.handle_request(job_id, data, process_func, path)