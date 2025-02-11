from routes.base_route_handler import BaseRouteHandler
from services.ffmpeg_toolkit import process_conversion

class MediaToMp3RouteHandler(BaseRouteHandler):
    """Handler for media to MP3 conversion requests"""
    
    def __init__(self):
        super().__init__('convert')
        self.create_route(
            path='/media-to-mp3',
            methods=['POST'],
            validation_schema={
                "type": "object",
                "properties": {
                    "media_url": {"type": "string", "format": "uri"},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "id": {"type": "string"},
                    "bitrate": {"type": "string", "pattern": "^[0-9]+k$"}
                },
                "required": ["media_url"],
                "additionalProperties": False
            },
            process_func=self.process_media_conversion
        )
        
    def process_media_conversion(self, job_id: str, data: dict) -> str:
        """Process media to MP3 conversion request
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            
        Returns:
            Path to converted MP3 file
        """
        media_url = data['media_url']
        bitrate = data.get('bitrate', '128k')
        
        self.logger.info(f"Job {job_id}: Converting {media_url} to MP3 with bitrate {bitrate}")
        return process_conversion(media_url, job_id, bitrate)

# Create and export the blueprint
convert_bp = MediaToMp3RouteHandler().blueprint