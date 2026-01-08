"""Face metadata database using shared engine."""

import logging
from typing import List, Optional

from sqlalchemy import delete, select

# Import shared database components
from eagle_eye.database import get_session
from eagle_eye.database.models import FaceMetadata

logger = logging.getLogger(__name__)


class MetadataStore:
    """Metadata database for face recognition (using shared engine)."""

    def get_or_create_person_id(self, name: str) -> int:
        """Get existing person ID or create new one."""
        with get_session() as session:
            # Try to get existing
            person = (
                session.exec(select(FaceMetadata).filter(FaceMetadata.name == name))
                .scalars()
                .first()
            )
            logger.debug(f"Person: {person}")
            if person:
                return person.id
            logger.debug(f"Person not found, creating new: {name}")
            # Create new
            person = FaceMetadata(name=name)
            session.add(person)
            session.commit()
            session.refresh(person)
            logger.debug(f"Person created: {person}")
            return person.id

    def get_person_name(self, person_id: int) -> Optional[str]:
        """Get person name by ID."""
        with get_session() as session:
            person = (
                session.exec(select(FaceMetadata).filter(FaceMetadata.id == person_id))
                .scalars()
                .first()
            )
            if person:
                return person.name
            return None

    def get_person_id(self, name: str) -> int:
        """Get ID for a person name."""
        with get_session() as session:
            persons = (
                session.exec(select(FaceMetadata).filter(FaceMetadata.name == name))
                .scalars()
                .first()
            )
            return persons.id

    def delete_person(self, name: str) -> int:
        """Delete person by name. Returns number of deleted records."""
        with get_session() as session:
            count = (
                session.exec(delete(FaceMetadata).filter(FaceMetadata.name == name))
                .scalars()
                .first()
            )
            session.commit()
            return count

    def get_all_persons(self) -> List[dict]:
        """Get all registered persons with their face counts."""
        with get_session() as session:
            persons = session.exec(select(FaceMetadata)).scalars().all()
            result = []
            for person in persons:
                result.append({"name": person.name, "id": person.id})
            return result
