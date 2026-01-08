import logging
import os
import uuid
from typing import List

import aiofiles
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from eagle_eye.config.folder_manager import MEDIA_DIR
from eagle_eye.database.models import Stream
from eagle_eye.database.sql import MediaStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/media", tags=["Media"])

# Media directory for storing uploaded files
VIDEO_DIR = MEDIA_DIR / "video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


# Get all media files
@router.get("/", response_model=List[Stream])
def get_media():
    """
    Get all media files.

    Returns:
        list[Stream]: List of all media files.
    """
    try:
        streams = MediaStore.get_all_streams()
        return streams
    except Exception as e:
        logger.error(f"Error getting media files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get media file by uid
@router.get("/{uid}", response_model=Stream)
def get_media_by_uid(uid: str):
    """
    Get media file by UID.

    Args:
        uid (str): The UID of the media file.

    Returns:
        Stream: The media file.
    """
    try:
        stream = MediaStore.get_stream_by_uid(uid)
        if not stream:
            raise HTTPException(status_code=404, detail="Media file not found")
        return stream
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting media file by uid: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=Stream)
async def upload_media(
    file: UploadFile = File(...),
    loop: bool = Query(False, description="Whether to loop the video"),
):
    """
    Upload a video file and register it for local streaming.

    Args:
        file (UploadFile): The uploaded video file from the client.
        loop (bool): Whether to loop the video.

    Returns:
        Stream: The created stream object with metadata.

    Workflow:
        1. Save the uploaded file to the VIDEO_DIR with a unique filename.
        2. Register the video in the database with a unique mount point.
        3. Return metadata stream object.
    """
    try:
        # Generate a unique filename for the uploaded file
        filename = file.filename
        file_uid = uuid.uuid4().hex
        safe_name = f"{file_uid}_{filename}"
        dest = VIDEO_DIR / safe_name

        logger.info(f"Uploading file: {filename} into {dest}")

        # Save file asynchronously in chunks
        async with aiofiles.open(dest, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # Read 1MB chunks
                if not chunk:
                    break
                await f.write(chunk)

        # Register the video in the database with a unique mount point
        mount_point = f"media://video/{file_uid}"

        # Use MediaStore to create the stream
        stream = MediaStore.create_stream(
            uid=file_uid,
            filename=filename,
            filepath=str(dest),
            mount=mount_point,
            loop=loop,
        )

        logger.info(f"Media uploaded successfully: {mount_point}")
        return stream

    except Exception as e:
        logger.error(f"Error uploading media file: {e}")
        # Clean up file if database operation failed
        if dest.exists():
            try:
                os.remove(dest)
            except Exception as e:
                logger.error(f"Error removing file: {dest}")
        raise HTTPException(status_code=500, detail=str(e))


# Remove media file by uid
@router.delete("/{uid}")
def remove_media_by_uid(uid: str):
    """
    Remove media file by UID.

    Args:
        uid (str): The UID of the media file.

    Returns:
        dict: Success message
    """
    try:
        # Get the stream to find the filepath
        stream = MediaStore.get_stream_by_uid(uid)
        if not stream:
            raise HTTPException(status_code=404, detail="Media file not found")

        # Remove the media file from the file system
        if os.path.exists(stream.filepath):
            os.remove(stream.filepath)
            logger.info(f"Removed file: {stream.filepath}")

        # Remove the media file from the database
        success = MediaStore.delete_stream(uid)
        if not success:
            raise HTTPException(
                status_code=404, detail="Media file not found in database"
            )

        return {"message": "Media file removed successfully", "uid": uid}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing media file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
