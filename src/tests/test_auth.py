import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.user import User
from src.models.token import BlacklistedToken
from src.utils.auth import create_access_token, create_refresh_token, get_password_hash
import jwt
from datetime import datetime, timedelta, timezone

client = TestClient(app)

# Test user data
test_user = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
}

@pytest.fixture
async def create_test_user():
    # Create a test user
    hashed_password = get_password_hash(test_user["password"])
    user = User(
        username=test_user["username"],
        email=test_user["email"],
        password_hash=hashed_password
    )
    await user.insert()
    yield user
    # Clean up
    await User.find_one({"email": test_user["email"]}).delete()
    await BlacklistedToken.find_many({}).delete_many()

def test_register():
    # Test user registration
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data

def test_login(create_test_user):
    # Test user login
    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["tokenType"] == "bearer"

def test_refresh_token(create_test_user):
    # First login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    refresh_token = login_response.json()["refreshToken"]
    
    # Use refresh token to get new tokens
    refresh_response = client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert data["tokenType"] == "bearer"
    
    # Old refresh token should be blacklisted
    # Try using it again should fail
    second_refresh = client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_token}
    )
    assert second_refresh.status_code == 401

def test_logout(create_test_user):
    # First login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    access_token = login_response.json()["accessToken"]
    
    # Logout
    logout_response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_response.status_code == 200
    
    # Try using the token after logout should fail
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 401

def test_get_me(create_test_user):
    # First login to get tokens
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    access_token = login_response.json()["accessToken"]
    
    # Get user profile
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]