import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.db import models, schemas
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
def admin_token(db):
    """Create admin user and return token"""
    admin_user = models.User(
        email="admin@example.com",
        hashed_password=auth_service.get_password_hash("adminpass"),
        full_name="Admin User",
        is_admin=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return auth_service.create_token(admin_user.id)

@pytest.fixture
def normal_token(db):
    """Create normal user and return token"""
    normal_user = models.User(
        email="user@example.com",
        hashed_password=auth_service.get_password_hash("userpass"),
        full_name="Normal User",
        is_admin=False
    )
    db.add(normal_user)
    db.commit()
    db.refresh(normal_user)
    
    return auth_service.create_token(normal_user.id)

@pytest.fixture
def test_category(db):
    """Create a test category"""
    category = models.Category(
        name="Test Category",
        description="Test category description"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@pytest.fixture
def test_product(db, test_category):
    """Create a test product"""
    product = models.Product(
        name="Test Product",
        description="Test product description",
        price=99.99,
        stock=10,
        image_url="http://example.com/image.jpg",
        category_id=test_category.id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


class TestProductEndpoints:
    """Test product endpoints"""
    
    def test_read_products_empty(self):
        """Test reading products when none exist"""
        response = client.get("/api/products/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_read_products(self, test_product):
        """Test reading products when one exists"""
        response = client.get("/api/products/")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Test Product"
    
    def test_read_product_by_id(self, test_product):
        """Test reading a single product by ID"""
        response = client.get(f"/api/products/{test_product.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Product"
        assert response.json()["price"] == 99.99
    
    def test_read_product_not_found(self):
        """Test reading a non-existent product"""
        response = client.get("/api/products/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"
    
    def test_create_product_as_admin(self, admin_token, test_category):
        """Test creating a product as admin"""
        product_data = {
            "name": "New Product",
            "description": "New product description",
            "price": 49.99,
            "stock": 5,
            "image_url": "http://example.com/new.jpg",
            "category_id": test_category.id
        }
        
        response = client.post(
            "/api/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Product"
        assert data["price"] == 49.99
        assert "id" in data
    
    def test_create_product_as_non_admin(self, normal_token, test_category):
        """Test creating a product as non-admin (should fail)"""
        product_data = {
            "name": "New Product",
            "description": "New product description",
            "price": 49.99,
            "stock": 5,
            "image_url": "http://example.com/new.jpg",
            "category_id": test_category.id
        }
        
        response = client.post(
            "/api/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_create_product_invalid_category(self, admin_token):
        """Test creating a product with invalid category"""
        product_data = {
            "name": "New Product",
            "description": "New product description",
            "price": 49.99,
            "stock": 5,
            "image_url": "http://example.com/new.jpg",
            "category_id": 999  # Non-existent category
        }
        
        response = client.post(
            "/api/products/",
            json=product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Category not found"
    
    def test_update_product(self, admin_token, test_product):
        """Test updating a product"""
        update_data = {
            "name": "Updated Product",
            "price": 150.99
        }
        
        response = client.put(
            f"/api/products/{test_product.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
        assert data["price"] == 150.99
        assert data["description"] == "Test product description"  # Unchanged
    
    def test_update_product_not_found(self, admin_token):
        """Test updating a non-existent product"""
        update_data = {"name": "Updated Product"}
        
        response = client.put(
            "/api/products/999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
    
    def test_delete_product(self, admin_token, test_product):
        """Test deleting a product"""
        response = client.delete(
            f"/api/products/{test_product.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.json() is True
        
        # Verify it's deleted
        get_response = client.get(f"/api/products/{test_product.id}")
        assert get_response.status_code == 404
    
    def test_delete_product_not_found(self, admin_token):
        """Test deleting a non-existent product"""
        response = client.delete(
            "/api/products/999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404


class TestCategoryEndpoints:
    """Test category endpoints"""
    
    def test_read_categories_empty(self):
        """Test reading categories when none exist"""
        response = client.get("/api/products/categories/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_read_categories(self, test_category):
        """Test reading categories when one exists"""
        response = client.get("/api/products/categories/")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Test Category"
    
    def test_read_category_by_id(self, test_category):
        """Test reading a single category by ID"""
        response = client.get(f"/api/products/categories/{test_category.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test Category"
    
    def test_read_category_not_found(self):
        """Test reading a non-existent category"""
        response = client.get("/api/products/categories/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Category not found"
    
    def test_create_category_as_admin(self, admin_token):
        """Test creating a category as admin"""
        category_data = {
            "name": "New Category",
            "description": "New category description"
        }
        
        response = client.post(
            "/api/products/categories/",
            json=category_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Category"
        assert "id" in data
    
    def test_create_category_as_non_admin(self, normal_token):
        """Test creating a category as non-admin (should fail)"""
        category_data = {
            "name": "New Category",
            "description": "New category description"
        }
        
        response = client.post(
            "/api/products/categories/",
            json=category_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_update_category(self, admin_token, test_category):
        """Test updating a category"""
        update_data = {
            "name": "Updated Category",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/api/products/categories/{test_category.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["description"] == "Updated description"
    
    def test_delete_category(self, admin_token, test_category):
        """Test deleting a category"""
        response = client.delete(
            f"/api/products/categories/{test_category.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.json() is True
        
        # Verify it's deleted
        get_response = client.get(f"/api/products/categories/{test_category.id}")
        assert get_response.status_code == 404