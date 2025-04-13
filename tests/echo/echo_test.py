from starlette.testclient import TestClient
from echo.main import app

def test_echo():
    client = TestClient(app)
    test_data = b"Hello, world!"
    response = client.post("/", data=test_data)

    assert response.status_code == 200
    assert response.content == test_data
