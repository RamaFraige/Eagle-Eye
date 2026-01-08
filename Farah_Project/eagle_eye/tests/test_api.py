import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi.testclient import TestClient

from eagle_eye.interfaces.api.app import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
