from fastapi.testclient import TestClient

from backend import main

client = TestClient(main.app)


def test_read_main():
    """Test the read_main function."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == '"Hello world!"'
