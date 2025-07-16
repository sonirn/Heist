"""Video cleanup utilities."""

import os
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def schedule_video_cleanup(generation_id: str, video_path: str, delay_hours: int = 24):
    """Schedule cleanup of a video file after specified delay.
    
    Args:
        generation_id: ID of the generation
        video_path: Path to video file to cleanup
        delay_hours: Hours to wait before cleanup (default: 24)
    """
    try:
        # Schedule deletion as a background task instead of blocking
        asyncio.create_task(cleanup_video_after_delay(generation_id, video_path, delay_hours))
        logger.info(f"Scheduled cleanup for generation {generation_id}: {video_path} (in {delay_hours} hours)")
            
    except Exception as e:
        logger.error(f"Failed to schedule cleanup for generation {generation_id}: {e}")

async def cleanup_video_after_delay(generation_id: str, video_path: str, delay_hours: int = 24):
    """Cleanup video file after delay - runs as background task."""
    try:
        # Wait for the delay
        await asyncio.sleep(delay_hours * 3600)  # Convert hours to seconds
        
        # Check if file still exists
        if os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"Cleaned up video for generation {generation_id}: {video_path}")
        else:
            logger.info(f"Video already removed for generation {generation_id}: {video_path}")
            
    except Exception as e:
        logger.error(f"Failed to cleanup video for generation {generation_id}: {e}")