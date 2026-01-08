import logging
from typing import List

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from eagle_eye.database.models import FaceMetadata
from eagle_eye.database.vector import face_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/faces", tags=["Face"])


async def process_uploaded_image(file: UploadFile) -> np.ndarray:
    """
    Process an uploaded image file and convert it to a numpy array.

    Args:
        file: Uploaded image file from FastAPI

    Returns:
        Numpy array in BGR format (OpenCV format)
    """
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(
            status_code=400, detail=f"Invalid image file: {file.filename}"
        )

    return img


@router.post("/", summary="Add face(s) to database")
async def add_faces(
    name: str = Form(..., description="Name of the person"),
    images: List[UploadFile] = File(..., description="One or more face images"),
):
    """
    Add one or more face images for a person to the recognition database.

    Multiple images of the same person improve recognition accuracy.

    - **name**: Name of the person (required)
    - **images**: One or more image files containing the person's face (required)
    """
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required")

    try:
        # Process all uploaded images
        image_arrays = []
        for file in images:
            img_array = await process_uploaded_image(file)
            image_arrays.append(img_array)

        logger.info(f"Processing {len(image_arrays)} image(s) for {name}")

        # Add faces to database
        success = await face_db.add_face_batch(image_arrays, name)

        if success:
            face_count = face_db.get_face_count(name)
            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "message": f"Successfully added {len(image_arrays)} face(s) for {name}",
                    "name": name,
                    "total_faces": face_count,
                },
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to add faces. Please ensure images contain clear, visible faces.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding faces for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{name}", summary="Remove face from database")
async def remove_face(name: str):
    """
    Remove all face embeddings for a person from the database.

    - **name**: Name of the person to remove
    """
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    try:
        success = face_db.remove_face(name)

        if success:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": f"Successfully removed all faces for {name}",
                    "name": name,
                }
            )
        else:
            raise HTTPException(status_code=404, detail=f"No faces found for {name}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing faces for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/", summary="List all registered faces", response_model=list[FaceMetadata])
async def list_faces():
    """
    Get a list of all registered persons in the face recognition database.

    Returns the person name and the number of face embeddings stored for each.
    """
    try:
        faces: list[dict] = face_db.get_all_faces()
        logger.info(f"Total faces: {len(faces)}")
        logger.info(faces)
        return JSONResponse(
            content={"status": "success", "total_persons": len(faces), "faces": faces}
        )

    except Exception as e:
        logger.error(f"Error listing faces: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{name}", summary="Get face details")
async def get_face_details(name: str):
    """
    Get details for a specific person in the database.

    - **name**: Name of the person
    """
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    try:
        face_count = face_db.get_face_count(name)

        if face_count == 0:
            raise HTTPException(status_code=404, detail=f"No faces found for {name}")

        return JSONResponse(
            content={"status": "success", "name": name, "face_count": face_count}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting face details for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
