import base64
from fastapi.testclient import TestClient
from src.agent import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_ingest_accepts_frame():
    # Create a small fake jpeg payload
    data = base64.b64encode(b"\xff\xd8\xff\xd9").decode()
    r = client.post(
        "/ingest/frame",
        json={
            "pageUrl": "https://www.tiktok.com/@user/video/123",
            "ts": 0,
            "contentType": "image/jpeg",
            "frameB64": data,
        },
    )
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["bytes"] == 4


