import os
import subprocess
from typing import Optional
from services.file_management import download_file
from services.webhook import send_webhook

STORAGE_PATH = "/tmp/"

def get_duration(file_path: str) -> float:
    """Get duration of media file using ffprobe.
    
    Args:
        file_path: Path to media file
        
    Returns:
        Duration in seconds as float
        
    Raises:
        subprocess.CalledProcessError: If ffprobe fails
    """
    cmd = [
        'ffprobe', '-v', 'error', 
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, text=True)
    result.check_returncode()
    return float(result.stdout)

def build_ffmpeg_command(
    video_path: str,
    audio_path: str,
    output_path: str,
    video_vol: float,
    audio_vol: float,
    output_length: str
) -> list[str]:
    """Construct FFmpeg command for audio mixing.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Path for output file
        video_vol: Video volume level (0-100)
        audio_vol: Audio volume level (0-100)
        output_length: 'video' or 'audio' to determine output duration
        
    Returns:
        List of FFmpeg command arguments
    """
    video_duration = get_duration(video_path)
    audio_duration = get_duration(audio_path)
    output_duration = video_duration if output_length == 'video' else audio_duration

    cmd = ['ffmpeg', '-y']
    cmd.extend(['-i', video_path])
    cmd.extend(['-i', audio_path])

    if output_length == 'audio' and audio_duration > video_duration:
        cmd.extend(['-stream_loop', '-1'])

    audio_filter = f'[1:a]volume={audio_vol/100}'
    if output_length == 'video':
        audio_filter += f',atrim=duration={video_duration}'
    audio_filter += '[a]'
    
    cmd.extend([
        '-filter_complex', audio_filter,
        '-map', '0:v',
        '-map', '[a]',
        '-c:v', 'libx264' if output_length == 'audio' and audio_duration > video_duration else 'copy',
        '-c:a', 'aac',
        '-t', str(output_duration),
        output_path
    ])
    
    return cmd

def process_audio_mixing(
    video_url: str,
    audio_url: str, 
    video_vol: float,
    audio_vol: float,
    output_length: str,
    job_id: str,
    webhook_url: Optional[str] = None
) -> str:
    """Mix audio and video streams with specified volume levels.
    
    Args:
        video_url: URL of video file
        audio_url: URL of audio file
        video_vol: Video volume level (0-100)
        audio_vol: Audio volume level (0-100)
        output_length: 'video' or 'audio' to determine output duration
        job_id: Unique job identifier
        webhook_url: Optional URL for status updates
        
    Returns:
        Path to output file
        
    Raises:
        subprocess.CalledProcessError: If FFmpeg fails
        OSError: If file operations fail
    """
    try:
        # Download input files
        video_path = download_file(video_url, STORAGE_PATH)
        audio_path = download_file(audio_url, STORAGE_PATH)
        output_path = os.path.join(STORAGE_PATH, f"{job_id}.mp4")

        # Build and run FFmpeg command
        cmd = build_ffmpeg_command(video_path, audio_path, output_path,
                                  video_vol, audio_vol, output_length)
        subprocess.run(cmd, check=True)

        # Clean up input files
        os.remove(video_path)
        os.remove(audio_path)

        # Send webhook notification if configured
        if webhook_url:
            send_webhook(webhook_url, {
                'status': 'success',
                'output_path': output_path,
                'job_id': job_id
            })

        return output_path

    except Exception as e:
        if webhook_url:
            send_webhook(webhook_url, {
                'status': 'error',
                'error': str(e),
                'job_id': job_id
            })
        raise