from routes.base_route_handler import BaseRouteHandler
from services.extract_keyframes import process_keyframe_extraction
from services.cloud_storage import upload_file
from typing import List, Dict

class ExtractKeyframesRouteHandler(BaseRouteHandler):
    """Handler for keyframe extraction requests"""
    
    def __init__(self):
        super().__init__('extract_keyframes')
        self.create_route(
            path='/extract-keyframes',
            methods=['POST'],
            validation_schema={
                "type": "object",
                "properties": {
                    "video_url": {"type": "string", "format": "uri"},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "id": {"type": "string"}
                },
                "required": ["video_url"],
                "additionalProperties": False
            },
            process_func=self.process_keyframe_extraction
        )
        
    def process_keyframe_extraction(self, job_id: str, data: dict) -> Dict[str, List[Dict[str, str]]]:
        """Process keyframe extraction request
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            
        Returns:
            Dictionary containing list of image URLs
        """
        video_url = data.get('video_url')
        self.logger.info(f"Job {job_id}: Extracting keyframes from {video_url}")
        
        # Extract keyframes
        image_paths = process_keyframe_extraction(video_url, job_id)
        
        # Upload each keyframe and collect URLs
        image_urls = []
        for image_path in image_paths:
            cloud_url = upload_file(image_path)
            image_urls.append({"image_url": cloud_url})
            
        return {"image_urls": image_urls}

# Create and export the blueprint
extract_keyframes_bp = ExtractKeyframesRouteHandler().blueprint
