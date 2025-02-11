from routes.base_route_handler import BaseRouteHandler
from services.audio_mixing import process_audio_mixing

class AudioMixingRouteHandler(BaseRouteHandler):
    """Handler for audio mixing requests"""
    
    def __init__(self):
        super().__init__('audio_mixing')
        self.create_route(
            path='/audio-mixing',
            methods=['POST'],
            validation_schema={
                "type": "object",
                "properties": {
                    "video_url": {"type": "string", "format": "uri"},
                    "audio_url": {"type": "string", "format": "uri"},
                    "video_vol": {"type": "number", "minimum": 0, "maximum": 100},
                    "audio_vol": {"type": "number", "minimum": 0, "maximum": 100},
                    "output_length": {"type": "string", "enum": ["video", "audio"]},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "id": {"type": "string"}
                },
                "required": ["video_url", "audio_url"],
                "additionalProperties": False
            },
            process_func=self.process_audio_mixing
        )
        
    def process_audio_mixing(self, job_id: str, data: dict) -> str:
        """Process audio mixing request
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            
        Returns:
            Path to processed file
        """
        video_url = data.get('video_url')
        audio_url = data.get('audio_url')
        video_vol = data.get('video_vol', 100)
        audio_vol = data.get('audio_vol', 100)
        output_length = data.get('output_length', 'video')
        webhook_url = data.get('webhook_url')
        
        self.logger.info(f"Job {job_id}: Processing audio mixing for {video_url} and {audio_url}")
        return process_audio_mixing(
            video_url, audio_url, video_vol, audio_vol, output_length, job_id, webhook_url
        )

# Create and export the blueprint
audio_mixing_bp = AudioMixingRouteHandler().blueprint
