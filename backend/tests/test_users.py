import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.db import models
from app.services import auth_service

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def admin_user(db):
    """Create admin user and return the model"""
    admin_user = models.User(
        email="admin@example.com",
        hashed_password=auth_service.get_password_hash("adminpass"),
        full_name="Admin User",
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user

@pytest.fixture
def normal_user(db):
    """Create normal user and return the model"""
    normal_user = models.User(
        email="user@example.com",
        hashed_password=auth_service.get_password_hash("userpass"),
        full_name="Normal User",
        is_admin=False
    )
    db.add(normal_user)
    db.commit()
    db.refresh(normal_user)
    return normal_user

@pytest.fixture
def admin_token(admin_user):
    """Return token for admin user"""
    return auth_service.create_token(admin_user.id)

@pytest.fixture
def normal_token(normal_user):
    """Return token for normal user"""
    return auth_service.create_token(normal_user.id)


class TestUsersEndpoints:
    """Test users endpoints"""
    
    def test_read_users_me(self, normal_user, normal_token):
        """Test retrieving own user profile"""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == normal_user.email
        assert data["full_name"] == normal_user.full_name
        assert not data["is_admin"]
    
    def test_update_users_me(self, normal_token):
        """Test updating own user profile"""
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@example.com"
        }
        
        response = client.put(
            "/api/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"
    
    def test_read_users_as_admin(self, admin_token, normal_user):
        """Test reading all users as admin"""
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) >= 2  # At least admin and normal user
    
    def test_read_users_as_non_admin(self, normal_token):
        """Test reading all users as non-admin (should fail)"""
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_read_user_by_id_as_admin(self, admin_token, normal_user):
        """Test reading specific user by ID as admin"""
        response = client.get(
            f"/api/users/{normal_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == normal_user.email
        assert data["full_name"] == normal_user.full_name
    
    def test_read_user_by_id_as_non_admin(self, normal_token, admin_user):
        """Test reading specific user by ID as non-admin (should fail)"""
        response = client.get(
            f"/api/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_update_user_as_admin(self, admin_token, normal_user):
        """Test updating user as admin"""
        update_data = {
            "full_name": "Admin Updated",
            "is_active": False
        }
        
        response = client.put(
            f"/api/users/{normal_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Admin Updated"
        assert not data["is_active"]
    
    def test_delete_user_as_admin(self, admin_token, normal_user):
        """Test deleting user as admin"""
        response = client.delete(
            f"/api/users/{normal_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.json() is True
        
        # Verify user is deleted
        get_response = client.get(
            f"/api/users/{normal_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404
    
    def test_update_user_as_non_admin(self, normal_token, admin_user):
        """Test updating other user as non-admin (should fail)"""
        update_data = {
            "full_name": "Unauthorized Update",
        }
        
        response = client.put(
            f"/api/users/{admin_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_delete_user_as_non_admin(self, normal_token, admin_user):
        """Test deleting user as non-admin (should fail)"""
        response = client.delete(
            f"/api/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_read_non_existent_user(self, admin_token):
        """Test reading non-existent user"""
        response = client.get(
            "/api/users/999",  # Non-existent user ID
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_update_non_existent_user(self, admin_token):
        """Test updating non-existent user"""
        update_data = {
            "full_name": "Does Not Exist",
        }
        
        response = client.put(
            "/api/users/999",  # Non-existent user ID
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_delete_non_existent_user(self, admin_token):
        """Test deleting non-existent user"""
        response = client.delete(
            "/api/users/999",  # Non-existent user ID
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_read_users_with_pagination(self, admin_token, db):
        """Test reading users with pagination"""
        # Create extra users for pagination test
        for i in range(5):
            user = models.User(
                email=f"user{i}@example.com",
                hashed_password=auth_service.get_password_hash(f"password{i}"),
                full_name=f"Test User {i}",
                is_admin=False
            )
            db.add(user)
        db.commit()
        
        # Test with limit=3
        response = client.get(
            "/api/users/?skip=0&limit=3",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 3
        
        # Test with skip=2
        response = client.get(
            "/api/users/?skip=2&limit=3",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 3
    
    def test_unauthorized_access(self):
        """Test accessing endpoints without token"""
        # Test accessing user list without token
        response = client.get("/api/users/")
        assert response.status_code == 401
        
        # Test accessing own profile without token
        response = client.get("/api/users/me")
        assert response.status_code == 401
        
        # Test updating own profile without token
        response = client.put(
            "/api/users/me",
            json={"full_name": "No Token"}
        )
        assert response.status_code == 401
        
        # Test accessing specific user without token
        response = client.get("/api/users/1")
        assert response.status_code == 401