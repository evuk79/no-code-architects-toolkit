import os
import ffmpeg
import logging
import requests
import subprocess
from typing import Dict, Any, Optional
from services.file_management import download_file

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

STORAGE_PATH = "/tmp/"
FONTS_DIR = '/usr/share/fonts/custom'

class CaptionProcessor:
    """Class to handle video captioning operations."""
    
    def __init__(self):
        self.font_paths = self._load_fonts()
        self.acceptable_fonts = list(self.font_paths.keys())

    def _load_fonts(self) -> Dict[str, str]:
        """Load available fonts from fonts directory."""
        font_paths = {}
        for font_file in os.listdir(FONTS_DIR):
            if font_file.lower().endswith('.ttf'):
                font_name = os.path.splitext(font_file)[0]
                font_paths[font_name] = os.path.join(FONTS_DIR, font_file)
        return font_paths

    def generate_style_line(self, options: Dict[str, Any]) -> str:
        """Generate ASS style line from options."""
        style_options = {
            'Name': 'Default',
            'Fontname': options.get('font_name', 'Arial'),
            'Fontsize': options.get('font_size', 12),
            'PrimaryColour': options.get('primary_color', '&H00FFFFFF'),
            'OutlineColour': options.get('outline_color', '&H00000000'),
            'BackColour': options.get('back_color', '&H00000000'),
            'Bold': options.get('bold', 0),
            'Italic': options.get('italic', 0),
            'Underline': options.get('underline', 0),
            'StrikeOut': options.get('strikeout', 0),
            'ScaleX': 100,
            'ScaleY': 100,
            'Spacing': 0,
            'Angle': 0,
            'BorderStyle': 1,
            'Outline': options.get('outline', 1),
            'Shadow': options.get('shadow', 0),
            'Alignment': options.get('alignment', 2),
            'MarginL': options.get('margin_l', 10),
            'MarginR': options.get('margin_r', 10),
            'MarginV': options.get('margin_v', 10),
            'Encoding': options.get('encoding', 1)
        }
        return f"Style: {','.join(str(v) for v in style_options.values())}"

    def process_captioning(
        self,
        file_url: str,
        caption_srt: str,
        caption_type: str,
        options: Dict[str, Any],
        job_id: str
    ) -> str:
        """Process video captioning using FFmpeg."""
        try:
            logger.info(f"Job {job_id}: Starting caption processing")
            
            # Download video file
            video_path = download_file(file_url, STORAGE_PATH)
            logger.info(f"Job {job_id}: Video downloaded to {video_path}")
            
            # Process caption file
            srt_path, caption_style = self._process_caption_file(
                caption_srt, caption_type, options, job_id)
            
            # Generate output path
            output_path = os.path.join(STORAGE_PATH, f"{job_id}_captioned.mp4")
            
            # Process video with captions
            self._add_captions_to_video(
                video_path, srt_path, output_path, options, job_id)
            
            # Clean up temporary files
            self._cleanup_files([video_path, srt_path])
            
            return output_path
            
        except Exception as e:
            logger.error(f"Job {job_id}: Error in caption processing - {str(e)}")
            raise

    def _process_caption_file(
        self,
        caption_srt: str,
        caption_type: str,
        options: Dict[str, Any],
        job_id: str
    ) -> tuple[str, str]:
        """Process and save caption file."""
        subtitle_extension = '.' + caption_type
        srt_path = os.path.join(STORAGE_PATH, f"{job_id}{subtitle_extension}")
        caption_style = ""

        if caption_type == 'ass':
            style_string = self.generate_style_line(options)
            caption_style = f"""
[Script Info]
Title: Highlight Current Word
ScriptType: v4.00+
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_string}
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            logger.info(f"Job {job_id}: Generated ASS style string")

        if caption_srt.startswith("https"):
            response = requests.get(caption_srt)
            response.raise_for_status()
            content = caption_style + (response.text if caption_type != 'ass' else response.content)
        else:
            content = caption_style + caption_srt

        with open(srt_path, 'w') as srt_file:
            srt_file.write(content)
            
        return srt_path, caption_style

    def _add_captions_to_video(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        options: Dict[str, Any],
        job_id: str
    ) -> None:
        """Add captions to video using FFmpeg."""
        font_name = options.get('font_name', 'Arial')
        selected_font = self.font_paths.get(font_name, self.font_paths['Arial'])
        
        if srt_path.endswith('.ass'):
            subtitle_filter = f"subtitles='{srt_path}'"
        else:
            style_options = {
                'FontName': font_name,
                'FontSize': options.get('font_size', 24),
                'PrimaryColour': options.get('primary_color', '&H00FFFFFF'),
                'SecondaryColour': options.get('secondary_color', '&H00000000'),
                'OutlineColour': options.get('outline_color', '&H00000000'),
                'BackColour': options.get('back_color', '&H00000000'),
                'Bold': options.get('bold', 0),
                'Italic': options.get('italic', 0),
                'Underline': options.get('underline', 0),
                'StrikeOut': options.get('strikeout', 0),
                'Alignment': options.get('alignment', 2),
                'MarginV': options.get('margin_v', 10),
                'MarginL': options.get('margin_l', 10),
                'MarginR': options.get('margin_r', 10),
                'Outline': options.get('outline', 1),
                'Shadow': options.get('shadow', 0),
                'Blur': options.get('blur', 0),
                'BorderStyle': options.get('border_style', 1),
                'Encoding': options.get('encoding', 1),
                'Spacing': options.get('spacing', 0),
                'Angle': options.get('angle', 0),
                'UpperCase': options.get('uppercase', 0)
            }
            subtitle_filter = f"subtitles={srt_path}:force_style='" + \
                ','.join(f"{k}={v}" for k, v in style_options.items() if v is not None) + "'"

        try:
            ffmpeg.input(video_path).output(
                output_path,
                vf=subtitle_filter,
                acodec='copy'
            ).run()
            logger.info(f"Job {job_id}: Captions added successfully")
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode('utf8') if e.stderr else 'Unknown FFmpeg error'
            logger.error(f"Job {job_id}: FFmpeg error - {error_msg}")
            raise

    def _cleanup_files(self, files: list[str]) -> None:
        """Clean up temporary files."""
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as e:
                logger.warning(f"Error removing file {file_path}: {str(e)}")

def process_captioning(
    file_url: str,
    caption_srt: str,
    caption_type: str,
    options: Dict[str, Any],
    job_id: str
) -> str:
    """Public interface for caption processing."""
    processor = CaptionProcessor()
    return processor.process_captioning(
        file_url, caption_srt, caption_type, options, job_id)
