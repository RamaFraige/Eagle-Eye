from unittest.mock import MagicMock, patch

import pytest

from eagle_eye.database.models import Stream
from eagle_eye.database.sql.media_store import MediaStore


@pytest.fixture
def mock_session():
    with patch("eagle_eye.database.sql.media_store.get_session") as mock_get_session:
        session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = session
        yield session


def test_media_store_create_stream(mock_session):
    # Setup
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()

    # Execute
    stream = MediaStore.create_stream(
        uid="123",
        filename="video.mp4",
        filepath="/tmp/video.mp4",
        mount="media://test",
        loop=True,
    )

    # Verify
    assert stream.uid == "123"
    assert stream.filename == "video.mp4"
    assert stream.filepath == "/tmp/video.mp4"
    assert stream.mount == "media://test"
    assert stream.loop is True
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


def test_media_store_get_stream_by_mount(mock_session):
    # Setup
    mock_stream = Stream(uid="123", mount="media://test", filepath="/path")
    mock_session.exec.return_value.first.return_value = mock_stream

    # Execute
    result = MediaStore.get_stream_by_mount("media://test")

    # Verify
    assert result == mock_stream
    mock_session.exec.assert_called_once()


def test_media_store_handle_url(mock_session):
    # Setup
    mock_stream = Stream(
        uid="123", mount="media://test", filepath="/resolved/path", loop=True
    )
    mock_session.exec.return_value.first.return_value = mock_stream

    # Execute - Case 1: Custom schema
    resolved, loop = MediaStore.handle_url("media://test")
    assert resolved == "/resolved/path"
    assert loop is True

    # Execute - Case 2: Regular path
    resolved, loop = MediaStore.handle_url("/regular/path")
    assert resolved == "/regular/path"
    assert loop is False


def test_stream_model_defaults():
    # Setup
    stream = Stream(
        uid="123",
        mount="media://test",
    )

    # Verify defaults
    assert stream.loop is False
    assert stream.created_at is not None
    assert stream.updated_at is None
