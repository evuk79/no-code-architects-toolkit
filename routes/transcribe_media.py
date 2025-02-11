from routes.base_route_handler import BaseRouteHandler
from services.transcription import process_transcription
from services.cloud_storage import upload_file
import os

class TranscribeMediaRouteHandler(BaseRouteHandler):
    """Handler for media transcription requests"""
    
    def __init__(self):
        super().__init__('transcribe')
        self.create_route(
            path='/transcribe-media',
            methods=['POST'],
            validation_schema={
                "type": "object",
                "properties": {
                    "media_url": {"type": "string", "format": "uri"},
                    "output": {"type": "string", "enum": ["transcript", "srt", "vtt", "ass"]},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "max_chars": {"type": "integer"},
                    "id": {"type": "string"}
                },
                "required": ["media_url"],
                "additionalProperties": False
            },
            process_func=self.process_transcription
        )
        
    def process_transcription(self, job_id: str, data: dict) -> str:
        """Process media transcription request
        
        Args:
            job_id: Unique job identifier
            data: Request payload
            
        Returns:
            Either the transcript text or path to transcript file
        """
        media_url = data['media_url']
        output = data.get('output', 'transcript')
        max_chars = data.get('max_chars', 56)
        
        self.logger.info(f"Job {job_id}: Transcribing {media_url} with output format {output}")
        
        # Process transcription
        result = process_transcription(media_url, output, max_chars)
        
        # Handle file-based outputs
        if output in ['srt', 'vtt', 'ass']:
            try:
                # Upload the file and clean up
                cloud_url = upload_file(result)
                os.remove(result)
                return cloud_url
            except Exception as e:
                # Clean up if upload fails
                if os.path.exists(result):
                    os.remove(result)
                raise
                
        return result

# Create and export the blueprint
transcribe_bp = TranscribeMediaRouteHandler().blueprint
