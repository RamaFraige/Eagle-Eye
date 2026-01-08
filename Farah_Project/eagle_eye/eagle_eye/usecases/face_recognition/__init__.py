from .usecase import FaceRecognition

# from .vector_db import face_db


# def add_face(image, name: str) -> bool:
#     """Add a face to the database."""
#     return face_db.add_face(image, name)


# def remove_face(name: str) -> bool:
#     """Remove a face from the database."""
#     return face_db.remove_face(name)


__all__ = [
    "FaceRecognition",
    "face_db",
    "add_face",
    "remove_face",
]
