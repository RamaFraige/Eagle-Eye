"""Media store service - handles media management and URL resolution."""

from typing import List, Optional, Tuple

from sqlmodel import select

from eagle_eye.database import get_session
from eagle_eye.database.models import Stream


class MediaStore:
    """Service for managing media streams."""

    @staticmethod
    def create_stream(
        uid: str, filename: str, filepath: str, mount: str, loop: bool = False
    ) -> Stream:
        """
        Create a new media stream entry.

        Args:
            uid: Unique identifier for the stream
            filename: Name of the media file
            filepath: Full path to the media file
            mount: Mount point (e.g., media://stream_id)
            loop: Whether to loop the stream
        """
        with get_session() as session:
            stream = Stream(
                uid=uid, filename=filename, filepath=filepath, mount=mount, loop=loop
            )
            session.add(stream)
            session.commit()
            session.refresh(stream)
            return stream

    @staticmethod
    def get_stream_by_mount(mount: str) -> Optional[Stream]:
        """Get stream by mount point."""
        with get_session() as session:
            stmt = select(Stream).where(Stream.mount == mount)
            return session.exec(stmt).first()

    @staticmethod
    def get_stream_by_uid(uid: str) -> Optional[Stream]:
        """Get stream by UID."""
        with get_session() as session:
            stmt = select(Stream).where(Stream.uid == uid)
            return session.exec(stmt).first()

    @staticmethod
    def get_all_streams() -> List[Stream]:
        """Get all streams."""
        with get_session() as session:
            stmt = select(Stream)
            return list(session.exec(stmt).all())

    @staticmethod
    def delete_stream(uid: str) -> bool:
        """Delete a stream by UID."""
        with get_session() as session:
            stream = session.exec(select(Stream).where(Stream.uid == uid)).first()
            if stream:
                session.delete(stream)
                session.commit()
                return True
            return False

    @staticmethod
    def handle_url(url: str) -> Tuple[str, bool]:
        """
        Replace custom schemas (e.g., media://) with actual folder paths.

        Args:
            url: URL to process (can be media:// URL or regular path)

        Returns:
            Tuple of (resolved_path, loop_enabled)
        """
        if url.startswith("media://"):
            stream = MediaStore.get_stream_by_mount(url)
            if stream:
                return stream.filepath, stream.loop
            # If media_id not found, return original URL with no loop
        return url, False

    @staticmethod
    def get_media_filepath(media_url: str) -> Optional[Tuple[str, bool]]:
        """
        Retrieves the actual file path for a given media URL from the database.

        Args:
            media_url: Media URL (e.g., media://stream_id)

        Returns:
            Tuple of (filepath, loop) or None if not found
        """
        stream = MediaStore.get_stream_by_mount(media_url)
        if stream:
            return stream.filepath, stream.loop
        return None


# Create a global instance
media_store = MediaStore()
