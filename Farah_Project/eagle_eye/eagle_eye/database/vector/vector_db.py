import asyncio
import logging
from typing import List, Optional, Tuple

import faiss
import numpy as np
from deepface import DeepFace

from eagle_eye.config.folder_manager import VECTOR_DIR
from eagle_eye.database.sql.metadata_store import MetadataStore

logger = logging.getLogger(__name__)


class FaceDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._index: Optional[faiss.Index] = None
        self._model_name = "VGG-Face"

        # Persistence paths
        self._index_file = VECTOR_DIR / "faiss_index.bin"

        # Initialize metadata database (uses shared engine)
        self._metadata_db: Optional[MetadataStore] = None

    def _ensure_db_loaded(self):
        """Load database from disk if not already loaded."""
        if self._index is None:
            VECTOR_DIR.mkdir(parents=True, exist_ok=True)

            # Load FAISS Index
            if self._index_file.exists():
                try:
                    self._index = faiss.read_index(str(self._index_file))
                    logger.info(f"Loaded FAISS index from {self._index_file}")
                except Exception as e:
                    logger.error(f"Failed to load FAISS index: {e}")
                    self._index = None

        if self._metadata_db is None:
            # Use shared database engine (no path needed)
            self._metadata_db = MetadataStore()

        self._initialized = True

    async def _save_index_async(self):
        """Save FAISS index to disk asynchronously."""
        # Ensure index is loaded
        self._ensure_db_loaded()
        try:
            VECTOR_DIR.mkdir(parents=True, exist_ok=True)

            if self._index is not None:
                # Use run_in_executor for CPU-bound FAISS write operation
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, faiss.write_index, self._index, str(self._index_file)
                )
                logger.info("Saved FAISS index to disk")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def _save_index(self):
        """Save FAISS index to disk (synchronous wrapper)."""
        try:
            asyncio.run(self._save_index_async())
        except RuntimeError:
            # If event loop is already running, use sync version
            self._save_index_sync()

    def _save_index_sync(self):
        """Save FAISS index to disk (synchronous)."""
        self._ensure_db_loaded()
        try:
            VECTOR_DIR.mkdir(parents=True, exist_ok=True)
            if self._index is not None:
                faiss.write_index(self._index, str(self._index_file))
                logger.info("Saved FAISS index to disk (sync)")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def _init_index(self, dimension: int):
        """Initialize FAISS index with ID mapping."""
        if self._index is None:
            self._index = faiss.IndexIDMap(faiss.IndexFlatL2(dimension))

    async def add_face_batch(self, images: List[str], name: str) -> bool:
        """
        Add multiple faces for the same person to the vector database.

        Args:
            images: List of image paths or numpy arrays (BGR).
            name: Name of the person.

        Returns:
            True if at least one face was added successfully, False otherwise.
        """
        # Ensure index is loaded
        self._ensure_db_loaded()

        if not images:
            logger.warning(f"No images provided for {name}")
            return False

        try:
            # Get or create person ID (reuses existing ID if name exists)
            person_id = self._metadata_db.get_or_create_person_id(name)

            embeddings_list = []
            successful_count = 0

            # Process each image and collect embeddings
            for idx, image in enumerate(images):
                try:
                    # Generate embedding
                    embeddings = DeepFace.represent(
                        img_path=image,
                        model_name=self._model_name,
                        enforce_detection=True,
                    )

                    if embeddings:
                        # Take the first detected face
                        embedding = embeddings[0]["embedding"]
                        embeddings_list.append(embedding)
                        successful_count += 1
                        logger.info(
                            f"Processed image {idx + 1}/{len(images)} for {name}"
                        )
                    else:
                        logger.warning(
                            f"No face detected in image {idx + 1} for {name}"
                        )

                except Exception as e:
                    logger.warning(f"Failed to process image {idx + 1} for {name}: {e}")
                    continue

            if not embeddings_list:
                logger.error(
                    f"No faces detected in any of the {len(images)} images for {name}"
                )
                return False

            # Initialize index if needed
            dim = len(embeddings_list[0])
            if self._index is None:
                self._init_index(dim)

            # Convert embeddings to numpy array
            vectors = np.array(embeddings_list, dtype="float32")

            # Create person IDs array (same ID for all embeddings)
            person_ids = np.array([person_id] * len(embeddings_list))

            # Add all vectors to index
            self._index.add_with_ids(vectors, person_ids)

            # Save the index asynchronously
            await self._save_index_async()

            logger.info(
                f"Added {successful_count}/{len(images)} face(s) for {name} with ID {person_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error adding faces for {name}: {e}")
            import traceback

            traceback.print_exc()
            return False

    def add_face(self, image: str, name: str) -> bool:
        """
        Add a face to the vector database (single image).

        Args:
            image: Image path or numpy array (BGR).
            name: Name of the person.
        """
        # Ensure index is loaded
        self._ensure_db_loaded()

        try:
            # Generate embedding
            embeddings = DeepFace.represent(
                img_path=image, model_name=self._model_name, enforce_detection=True
            )

            if not embeddings:
                logger.warning(f"No face detected in image for {name}")
                return False

            # Take the first detected face
            embedding = embeddings[0]["embedding"]
            dim = len(embedding)

            if self._index is None:
                self._init_index(dim)

            # Get or create person ID (reuses existing ID if name exists)
            person_id = self._metadata_db.get_or_create_person_id(name)

            logger.debug(f"Adding face for {name} with ID {person_id}")

            vector = np.array([embedding], dtype="float32")

            # Add to index with person ID
            self._index.add_with_ids(vector, np.array([person_id]))

            # Save only the index
            self._save_index()

            logger.info(f"Added face for {name} with ID {person_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding face: {e}")
            import traceback

            traceback.print_exc()
            return False

    def remove_face(self, name: str) -> bool:
        """Remove all faces for a person from the database by name."""
        # Ensure index is loaded
        self._ensure_db_loaded()
        try:
            if self._index is None:
                return False

            # Get all IDs for this person
            person_ids = self._metadata_db.get_person_ids(name)

            if not person_ids:
                logger.warning(f"No face found for {name}")
                return False

            # Remove from FAISS index
            self._index.remove_ids(np.array(person_ids))

            # Remove from metadata database
            self._metadata_db.delete_person(name)

            # Save index
            self._save_index()

            logger.info(f"Removed {len(person_ids)} face(s) for {name}")
            return True
        except Exception as e:
            logger.error(f"Error removing face: {e}")
            return False

    def search(
        self, vector: np.ndarray, threshold: float = 0.5
    ) -> Optional[Tuple[str, float]]:
        """
        Search for a face in the database.

        Args:
            vector: Face embedding vector to search for
            threshold: Similarity threshold (0-1). Higher = more strict matching.
                      Higher values mean better match (inverted from distance).

        Returns:
            Tuple of (name, similarity) or None
        """
        # Ensure index is loaded first
        self._ensure_db_loaded()

        if self._index is not None:
            if self._index.ntotal == 0:
                return None

        try:
            if self._index is None:
                return None

            distances, ids = self._index.search(vector, 1)
            distance = distances[0][0]

            # Convert distance to similarity score (invert it)
            # For normalized L2 distance, max distance is ~2
            # Similarity = 1 - (distance / 2)
            # So: distance=0 → similarity=1.0 (perfect match)
            #     distance=2 → similarity=0.0 (completely different)
            similarity = 1.0 - (distance / 2.0)

            if similarity > threshold:
                found_id = int(ids[0][0])
                if found_id != -1:
                    if self._metadata_db is None:
                        return None
                    name = self._metadata_db.get_person_name(found_id)
                    if name:
                        return name, similarity
        except Exception as e:
            logger.warning(f"Search failed: {e}")

        return None

    def get_all_faces(self) -> List[dict]:
        """
        Get all registered faces with their counts.

        Returns:
            List of dicts with 'name' and 'count' keys
        """
        self._ensure_db_loaded()

        if self._metadata_db is None:
            return []

        persons = self._metadata_db.get_all_persons()
        for person in persons:
            person["count"] = self.get_face_count_by_id(person["id"])
        return persons

    def get_face_count(self, name: str) -> int:
        """
        Get the number of face embeddings for a person.

        Args:
            name: Name of the person

        Returns:
            Number of face embeddings registered for this person
        """
        person_id = self._metadata_db.get_person_id(name)
        return self.get_face_count_by_id(person_id)

    def get_face_count_by_id(self, person_id: int) -> int:
        """
        Get the number of face embeddings for a person by ID
        by counting occurrences in the FAISS index.

        Args:
            person_id: ID of the person

        Returns:
            Number of face embeddings registered for this person
        """
        self._ensure_db_loaded()

        if self._index is None or self._index.ntotal == 0:
            return 0

        try:
            # IndexIDMap stores IDs internally
            ids = self._index.id_map  # type: ignore[attr-defined]

            # Convert to numpy array and count matches
            ids_np = faiss.vector_to_array(ids)
            return int(np.sum(ids_np == person_id))

        except Exception as e:
            logger.error(f"Failed to count faces for ID {person_id}: {e}")
            return 0

    @property
    def model_name(self) -> str:
        return self._model_name


# Global instance
face_db = FaceDatabase()
