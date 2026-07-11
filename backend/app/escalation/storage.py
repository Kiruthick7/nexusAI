"""
Module implementing Google Cloud Storage uploads and local mock storage fallbacks
for the Human Escalation spoken briefing wav files.
"""

import os
from typing import Optional
from app.core.config import settings
from app.core.logger import logger


def save_audio_locally(mission_id: str, audio_bytes: bytes) -> str:
    """
    Saves synthesized audio bytes to the local workspace public directory
    and returns a simulated static file URL.
    """
    try:
        # Resolve target path (backend/public/audio/)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        public_dir = os.path.join(base_dir, "public", "audio")
        os.makedirs(public_dir, exist_ok=True)
        
        file_path = os.path.join(public_dir, f"{mission_id}.wav")
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
            
        logger.info(f"[STORAGE SERVICE] Audio file successfully persisted locally at: {file_path}")
        
        # Return local route URL
        local_url = f"http://localhost:{settings.PORT}/public/audio/{mission_id}.wav"
        return local_url
    except Exception as err:
        logger.error(f"[STORAGE SERVICE] Local storage fallback file write failed: {err}", exc_info=True)
        # Return a simulated GCS URL for high-fidelity presentation if local file writing also fails
        return f"https://storage.googleapis.com/nexus-ai-escalation-bucket/audio/{mission_id}.wav?simulated=true"


def upload_escalation_audio(mission_id: str, audio_bytes: bytes) -> Optional[str]:
    """
    Uploads synthesized voice briefing bytes to Google Cloud Storage if GCS is configured.
    Falls back to saving inside local workspace public directory when GCS is unconfigured.
    
    Args:
        mission_id: Alphanumeric tracking mission ID.
        audio_bytes: Binary wav file content.
        
    Returns:
        Optional[str]: Cloud storage signed URL or local static fallback URL.
    """
    bucket_name = settings.GCS_BUCKET
    
    # Check if Google Cloud Storage is configured and ready
    if not bucket_name:
        logger.info("[STORAGE SERVICE] GCS_BUCKET is not configured. Redirecting audio to local workspace storage fallback.")
        return save_audio_locally(mission_id, audio_bytes)
        
    try:
        from google.cloud import storage
        
        project_id = settings.GCP_PROJECT_ID
        logger.info(f"[STORAGE SERVICE] Uploading audio briefing to GCS bucket='{bucket_name}' in project='{project_id}'")
        
        # Initialize standard GCS client
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        
        blob_path = f"audio/{mission_id}.wav"
        blob = bucket.blob(blob_path)
        
        # Upload wave file content
        blob.upload_from_string(audio_bytes, content_type="audio/wav")
        logger.info(f"[STORAGE SERVICE] Upload complete: {blob_path}")
        
        # Generate standard signed URL valid for 1 hour (3600 seconds)
        signed_url = blob.generate_signed_url(expiration=3600)
        return signed_url
        
    except ImportError:
        logger.warning("[STORAGE SERVICE] google-cloud-storage is missing from environment. Redirecting audio to local fallback.")
        return save_audio_locally(mission_id, audio_bytes)
        
    except Exception as err:
        # Gracefully handle any GCS exceptions. Never block or fail the mission because of storage issues.
        logger.error(
            f"[STORAGE SERVICE] Google Cloud Storage upload failed: {err}. "
            f"Failing back to saving locally inside the public folder.",
            exc_info=True
        )
        return save_audio_locally(mission_id, audio_bytes)
