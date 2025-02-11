from routes.base_route_handler import BaseRouteHandler
from services.image_to_video import process_image_to_video

class ImageToVideoRouteHandler(BaseRouteHandler):
    """Handler for image to video conversion requests"""
    
    def __init__(self):
        super().__init__('image_to_video')
        self.create_route(
            path='/image-to-video',
            methods=['POST'],
            validation_schema={
                "type": "object",
                "properties": {
                    "image_url": {"type": "string", "format": "uri"},
                    "length": {"type": "number", "minimum": 1, "maximum": 60},
                    "frame_rate": {"type": "integer", "minimum": 15, "maximum": 60},
                    "zoom_speed": {"type": "number", "minimum": 0, "maximum": 100},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "id": {"type": "string"}
                },
                "required": ["image_url"],
                "additionalProperties": False
            },
            process_func=self.process_image_to_video
        )
        
    def process_image_to_video(self, job_id: str, data: dict) -> str:
        """Process image to video conversion request
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            
        Returns:
            Path to converted video file
        """
        image_url = data.get('image_url')
        length = data.get('length', 5)
        frame_rate = data.get('frame_rate', 30)
        zoom_speed = data.get('zoom_speed', 3) / 100
        webhook_url = data.get('webhook_url')
        
        self.logger.info(f"Job {job_id}: Converting image {image_url} to video")
        return process_image_to_video(
            image_url, length, frame_rate, zoom_speed, job_id, webhook_url
        )

# Create and export the blueprint
image_to_video_bp = ImageToVideoRouteHandler().blueprint
