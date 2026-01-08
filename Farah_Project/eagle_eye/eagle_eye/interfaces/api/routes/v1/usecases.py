import asyncio
import logging
from typing import List

import cv2
import numpy as np
from fastapi import APIRouter
from fastrtc import register_webrtc
from fastrtc.models import Request

from eagle_eye.config.settings import settings
from eagle_eye.database.sql import MediaStore
from eagle_eye.usecases import USE_CASES, USE_CASES_LITERAL, get_use_case_color
from eagle_eye.usecases.pipe import build_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usecases")
usecase_router = APIRouter(tags=["UseCases"])


@usecase_router.get("/", response_model=List[str])
def get_usecases():
    return list(USE_CASES.keys())


def open_video(url: str):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        logger.error(f"Failed to open video source: {url}")
    return cap


async def video_frame_generator(url: str):
    url, loop = MediaStore.handle_url(url)
    cap = open_video(url)

    while True:
        if not cap or not cap.isOpened():
            await asyncio.sleep(0.3)
            cap = open_video(url)
            continue

        ret, frame = cap.read()
        if ret:
            yield frame
            continue

        if loop:
            logger.info("Loop enabled → restarting video")
            cap.release()
            cap = open_video(url)
            await asyncio.sleep(0.05)
        else:
            break


def stream_processor(use_cases: List[str]):
    pipeline = build_pipeline(tuple(use_cases))

    async def handler(request: Request, url: str):
        async for frame in video_frame_generator(url):
            annotated, result = pipeline(frame, stream_id=request.webrtc_id)
            yield annotated, result.model_dump()

    return handler


def live_processor(use_cases: List[str]):
    pipeline = build_pipeline(tuple(use_cases))

    async def handler(request: Request, frame: np.ndarray):
        annotated, result = pipeline(frame, stream_id=request.webrtc_id)
        yield annotated, result.model_dump()

    return handler


def register_usecase(
    prefix: str,
    handler,
    mode: str,
    title: str,
    name: str,
    color: str,
    default_input: dict | None = None,
):
    r = APIRouter(prefix=prefix, tags=[name.title()])

    register_webrtc(
        r,
        handler,
        mode=mode,
        ui_config={
            "title": title,
            "primary_color": color,
            **({"default_input": default_input} if default_input else {}),
        },
    )

    router.include_router(r)


def register_static_usecases():
    for name in USE_CASES:
        color = get_use_case_color(name)

        register_usecase(
            prefix=f"/{name}",
            handler=stream_processor([name]),
            mode="receive",
            title=f'<span class="text-[{color}]">{settings.APP_NAME}</span> {name}',
            name=name,
            color=color,
        )

        register_usecase(
            prefix=f"/{name}-live",
            handler=live_processor([name]),
            mode="send-receive",
            title=f'<span class="text-[{color}]">{settings.APP_NAME}</span> {name} Live',
            name=name,
            color=color,
        )


def register_dynamic_usecases():
    default_cases = ["face-detection", "guns-detection", "fight-detection"]

    def dynamic_handler(req: Request, url: str, use_cases: List[USE_CASES_LITERAL]):
        return stream_processor(use_cases)(req, url)

    def dynamic_live_handler(
        req: Request, frame: np.ndarray, use_cases: List[USE_CASES_LITERAL]
    ):
        return live_processor(use_cases)(req, frame)

    register_usecase(
        prefix="/dynamic",
        handler=dynamic_handler,
        mode="receive",
        title=f'<span class="text-blue-500">{settings.APP_NAME}</span> Dynamic',
        name="dynamic",
        color="#ce9178",
        default_input={"use_cases": default_cases},
    )

    register_usecase(
        prefix="/dynamic-live",
        handler=dynamic_live_handler,
        mode="send-receive",
        title=f'<span class="text-blue-500">{settings.APP_NAME}</span> Dynamic Live',
        name="dynamic",
        color="#ce9178",
        default_input={"use_cases": default_cases},
    )


router.include_router(usecase_router)
register_dynamic_usecases()
register_static_usecases()
