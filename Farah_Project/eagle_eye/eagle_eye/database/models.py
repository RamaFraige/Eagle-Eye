"""Consolidated database models for Eagle Eye."""

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel


class Stream(SQLModel, table=True):
    """Stream model representing a video file that can be streamed via Local Media."""

    id: Optional[int] = Field(default=None, primary_key=True)
    uid: str
    filename: str = PydanticField(..., exclude=True)  # <- exclude from response
    filepath: str = PydanticField(..., exclude=True)  # <- exclude from response
    mount: str
    loop: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FaceMetadata(SQLModel, table=True):
    """Face metadata model for storing person information."""

    __tablename__ = "faces"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., nullable=False, unique=True)
