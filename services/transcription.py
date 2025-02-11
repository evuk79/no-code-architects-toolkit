import os
import whisper
import srt
import logging
from datetime import timedelta
from typing import Optional, Union
from services.file_management import download_file

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

STORAGE_PATH = "/tmp/"

class TranscriptionProcessor:
    """Class to handle audio/video transcription."""
    
    def __init__(self):
        self.storage_path = STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Initialized transcription processor with storage path: {self.storage_path}")
        self.model = whisper.load_model("base")
        logger.info("Loaded Whisper model")

    def transcribe_media(
        self,
        media_url: str,
        output_type: str,
        max_chars: int = 56,
        language: Optional[str] = None
    ) -> Union[str, tuple[str, str]]:
        """Transcribe media and generate output in specified format.
        
        Args:
            media_url: URL of media file to transcribe
            output_type: Output format ('transcript', 'srt', 'vtt', 'ass')
            max_chars: Maximum characters per line for ASS format
            language: Optional language code for transcription
            
        Returns:
            Path to output file or transcript text
            
        Raises:
            ValueError: If invalid output type is specified
            Exception: For other errors
        """
        try:
            # Download media file
            input_filename = download_file(
                media_url,
                os.path.join(self.storage_path, 'input_media')
            )
            logger.info(f"Downloaded media to: {input_filename}")
            
            # Perform transcription
            result = self._perform_transcription(input_filename, language)
            
            # Generate output based on requested format
            if output_type == 'transcript':
                output = result['text']
                logger.info("Generated transcript output")
            elif output_type in ['srt', 'vtt']:
                output = self._generate_subtitles(result, output_type)
            elif output_type == 'ass':
                output = self._generate_ass_subtitles(result, max_chars)
            else:
                raise ValueError(f"Invalid output type: {output_type}")
            
            # Clean up input file
            self._cleanup_file(input_filename)
            
            return output
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise

    def _perform_transcription(
        self,
        input_filename: str,
        language: Optional[str] = None
    ) -> dict:
        """Perform transcription using Whisper model.
        
        Args:
            input_filename: Path to media file
            language: Optional language code for transcription
            
        Returns:
            Transcription result dictionary
        """
        logger.info("Starting transcription")
        result = self.model.transcribe(input_filename, language=language)
        logger.info("Transcription completed")
        return result

    def _generate_subtitles(
        self,
        result: dict,
        output_type: str
    ) -> str:
        """Generate subtitle file in SRT or VTT format.
        
        Args:
            result: Transcription result
            output_type: Output format ('srt' or 'vtt')
            
        Returns:
            Path to subtitle file
        """
        srt_subtitles = []
        for i, segment in enumerate(result['segments'], start=1):
            start = timedelta(seconds=segment['start'])
            end = timedelta(seconds=segment['end'])
            text = segment['text'].strip()
            srt_subtitles.append(srt.Subtitle(i, start, end, text))
        
        output_content = srt.compose(srt_subtitles)
        output_filename = os.path.join(self.storage_path, f"{uuid.uuid4()}.{output_type}")
        
        with open(output_filename, 'w') as f:
            f.write(output_content)
        
        logger.info(f"Generated {output_type.upper()} output: {output_filename}")
        return output_filename

    def _generate_ass_subtitles(
        self,
        result: dict,
        max_chars: int
    ) -> str:
        """Generate ASS subtitle file with word-level timestamps.
        
        Args:
            result: Transcription result
            max_chars: Maximum characters per line
            
        Returns:
            Path to ASS subtitle file
        """
        logger.info("Generating ASS subtitles")
        ass_content = self._create_ass_header()
        
        for segment in result['segments']:
            words = segment.get('words', [])
            if not words:
                continue
                
            lines = self._group_words_into_lines(words, max_chars)
            
            for line in lines:
                line_start_time = line[0]['start']
                line_end_time = line[-1]['end']
                
                for i, word_info in enumerate(line):
                    start_time = word_info['start']
                    end_time = line[i + 1]['start'] if i + 1 < len(line) else line_end_time
                    
                    caption_parts = [
                        r'{\c&H00FFFF&}' + w['word'] if w == word_info 
                        else r'{\c&HFFFFFF&}' + w['word'] 
                        for w in line
                    ]
                    caption_with_highlight = ' '.join(caption_parts)
                    
                    start = self._format_time(start_time)
                    end = self._format_time(end_time)
                    
                    ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{caption_with_highlight}\n"
        
        output_filename = os.path.join(self.storage_path, f"{uuid.uuid4()}.ass")
        with open(output_filename, 'w') as f:
            f.write(ass_content)
        
        logger.info(f"Generated ASS output: {output_filename}")
        return output_filename

    def _create_ass_header(self) -> str:
        """Create ASS file header.
        
        Returns:
            ASS header content
        """
        return """[Script Info]
Title: Highlight Current Word
ScriptType: v4.00+
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,12,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def _group_words_into_lines(
        self,
        words: list,
        max_chars: int
    ) -> list[list[dict]]:
        """Group words into lines based on max characters.
        
        Args:
            words: List of word dictionaries
            max_chars: Maximum characters per line
            
        Returns:
            List of grouped word lists
        """
        lines = []
        current_line = []
        current_line_length = 0
        
        for word_info in words:
            word_length = len(word_info['word']) + 1  # +1 for space
            if current_line_length + word_length > max_chars:
                lines.append(current_line)
                current_line = [word_info]
                current_line_length = word_length
            else:
                current_line.append(word_info)
                current_line_length += word_length
                
        if current_line:
            lines.append(current_line)
            
        return lines

    def _format_time(self, t: float) -> str:
        """Format time for ASS subtitles.
        
        Args:
            t: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        centiseconds = int(round((t - int(t)) * 100))
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def _cleanup_file(self, file_path: str) -> None:
        """Clean up a file.
        
        Args:
            file_path: Path to file to remove
            
        Raises:
            OSError: If file removal fails
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except OSError as e:
            logger.warning(f"Error removing file {file_path}: {str(e)}")
            raise

def process_transcription(
    media_url: str,
    output_type: str,
    max_chars: int = 56,
    language: Optional[str] = None
) -> Union[str, tuple[str, str]]:
    """Public interface for media transcription."""
    processor = TranscriptionProcessor()
    return processor.transcribe_media(media_url, output_type, max_chars, language)
