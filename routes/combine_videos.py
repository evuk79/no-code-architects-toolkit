from routes.base_route_handler import BaseRouteHandler
from services.ffmpeg_toolkit import process_video_combination

class CombineVideosRouteHandler(BaseRouteHandler):
    """Handler for video combination requests"""
    
    def __init__(self):
        super().__init__('combine')
        self.create_route(
            path='/combine-videos',
            methods=['POST'],
            validation_schema={
                "type": "object",
                "properties": {
                    "video_urls": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "video_url": {"type": "string", "format": "uri"}
                            },
                            "required": ["video_url"]
                        },
                        "minItems": 1
                    },
                    "webhook_url": {"type": "string", "format": "uri"},
                    "id": {"type": "string"}
                },
                "required": ["video_urls"],
                "additionalProperties": False
            },
            process_func=self.process_video_combination
        )
        
    def process_video_combination(self, job_id: str, data: dict) -> str:
        """Process video combination request
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            
        Returns:
            Path to combined video file
        """
        media_urls = data['video_urls']
        self.logger.info(f"Job {job_id}: Combining {len(media_urls)} videos")
        return process_video_combination(media_urls, job_id)

# Create and export the blueprint
combine_bp = CombineVideosRouteHandler().blueprint