import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.database import Base, get_db
from app.db import schemas
from app.services import auth_service, user_service

# Setup test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def test_db():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session for testing
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the tables after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as c:
        yield c
    
    # Reset dependency override
    app.dependency_overrides = {}

# Mock user data
test_user = schemas.UserCreate(
    email="test@example.com",
    password="securepassword123",
    full_name="Test User"
)

class TestAuthRouter:
    
    def test_register_success(self, client, test_db):
        """Test successful user registration"""
        response = client.post(
            "/register",
            json={"email": test_user.email, "password": test_user.password, "full_name": test_user.full_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "id" in data
        
    def test_register_duplicate_email(self, client, test_db):
        """Test registration with already registered email"""
        # First registration
        client.post(
            "/register",
            json={"email": test_user.email, "password": test_user.password, "full_name": test_user.full_name}
        )
        
        # Second registration with same email
        response = client.post(
            "/register",
            json={"email": test_user.email, "password": "differentpassword", "full_name": "Another User"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"
    
    def test_login_success(self, client, test_db):
        """Test successful login"""
        # Register user first
        client.post(
            "/register",
            json={"email": test_user.email, "password": test_user.password, "full_name": test_user.full_name}
        )
        
        # Login
        response = client.post(
            "/login",
            data={"username": test_user.email, "password": test_user.password}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_db):
        """Test login with invalid credentials"""
        # Register user first
        client.post(
            "/register",
            json={"email": test_user.email, "password": test_user.password, "full_name": test_user.full_name}
        )
        
        # Login with wrong password
        response = client.post(
            "/login",
            data={"username": test_user.email, "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_test_token_endpoint(self, client, test_db):
        """Test the test-token endpoint with valid token"""
        # Register user
        register_response = client.post(
            "/register",
            json={"email": test_user.email, "password": test_user.password, "full_name": test_user.full_name}
        )
        user_id = register_response.json()["id"]
        
        # Login to get token
        login_response = client.post(
            "/login",
            data={"username": test_user.email, "password": test_user.password}
        )
        token = login_response.json()["access_token"]
        
        # Test token endpoint
        response = client.post(
            "/test-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == test_user.email
    
    def test_test_token_invalid_token(self, client, test_db):
        """Test the test-token endpoint with invalid token"""
        response = client.post(
            "/test-token",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()

    @patch('app.services.auth_service.create_token')
    def test_login_token_creation(self, mock_create_token, client, test_db):
        """Test that create_token is called with correct parameters"""
        # Set up the mock
        mock_token = "mocked_access_token"
        mock_create_token.return_value = mock_token
        
        # Register user
        register_response = client.post(
            "/register",
            json={"email": test_user.email, "password": test_user.password, "full_name": test_user.full_name}
        )
        user_id = register_response.json()["id"]
        
        # Login
        response = client.post(
            "/login",
            data={"username": test_user.email, "password": test_user.password}
        )
        
        # Verify mock was called correctly
        mock_create_token.assert_called_once_with(user_id)
        
        # Verify response contains mocked token
        assert response.status_code == 200
        assert response.json() == {"access_token": mock_token, "token_type": "bearer"}