from fastapi import APIRouter

from .face_recognition import router as face_recognition_router
from .media import router as media_router
from .usecases import router as usecases_router

router = APIRouter(prefix="/v1")

router.include_router(media_router)
router.include_router(face_recognition_router)
router.include_router(usecases_router)
