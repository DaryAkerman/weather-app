import pytest
from flask import Flask
from app import app

@pytest.fixture
def client():
    """
    Fixture to set up the Flask test client.
    """
    with app.test_client() as client:
        yield client

def test_home_route_status_code(client):
    """
    Test that the home route ("/") returns a 200 status code.
    """
    response = client.get("/")
    assert response.status_code == 200
