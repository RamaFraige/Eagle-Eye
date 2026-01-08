"""Shared database engine and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as AlchemySession
from sqlmodel import Session, SQLModel

from eagle_eye.config.folder_manager import SQL_DIR
from eagle_eye.config.settings import settings

# Global engine instance
engine = None


def init_db():
    """Initialize the database engine and create all tables."""
    global engine

    # Ensure SQL directory exists
    SQL_DIR.mkdir(parents=True, exist_ok=True)

    # Create shared engine
    db_uri = settings.DB_URI
    engine = create_engine(
        db_uri, echo=False, connect_args={"check_same_thread": False}
    )

    # Create all tables
    # SQLModel tables (Stream)
    SQLModel.metadata.create_all(engine)


def close_db():
    """Close the database engine."""
    global engine
    if engine is not None:
        engine.dispose()
        engine = None


@contextmanager
def get_session() -> Generator[AlchemySession, None, None]:
    """
    Get a database session.

    Yields:
        SQLModel session
    """
    if engine is None:
        raise Exception("Database not initialized. Call init_db() first.")

    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
