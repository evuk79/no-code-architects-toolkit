from routes.base_route_handler import BaseRouteHandler
from services.caption_video import process_captioning

class CaptionVideoRouteHandler(BaseRouteHandler):
    """Handler for video captioning requests"""
    
    def __init__(self):
        super().__init__('caption')
        self.create_route(
            path='/caption-video',
            methods=['POST'],
            validation_schema={
                "type": "object",
                "properties": {
                    "video_url": {"type": "string", "format": "uri"},
                    "srt": {"type": "string"},
                    "ass": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "option": {"type": "string"},
                                "value": {}
                            },
                            "required": ["option", "value"]
                        }
                    },
                    "webhook_url": {"type": "string", "format": "uri"},
                    "id": {"type": "string"}
                },
                "required": ["video_url"],
                "oneOf": [
                    {"required": ["srt"]},
                    {"required": ["ass"]}
                ],
                "additionalProperties": False
            },
            process_func=self.process_captioning
        )
        
    def process_captioning(self, job_id: str, data: dict) -> str:
        """Process video captioning request
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            
        Returns:
            Path to processed file
        """
        video_url = data['video_url']
        caption_srt = data.get('srt')
        caption_ass = data.get('ass')
        options = data.get('options', [])
        
        self.logger.info(f"Job {job_id}: Processing captioning for {video_url}")
        
        # Determine caption type and content
        captions, caption_type = self._determine_caption_type(caption_srt, caption_ass)
        
        return process_captioning(video_url, captions, caption_type, options, job_id)
        
    def _determine_caption_type(self, srt: Optional[str], ass: Optional[str]) -> tuple[str, str]:
        """Determine which caption format to use
        
        Args:
            srt: SRT caption content
            ass: ASS caption content
            
        Returns:
            Tuple of (caption content, caption type)
        """
        if ass is not None:
            return ass, "ass"
        return srt, "srt"

# Create and export the blueprint
caption_bp = CaptionVideoRouteHandler().blueprint
