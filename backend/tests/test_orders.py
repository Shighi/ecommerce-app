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

@pytest.fixture
def test_order(db, normal_user, test_product):
    """Create a test order"""
    order = models.Order(
        user_id=normal_user.id,
        status=models.OrderStatus.PENDING,
        total_amount=test_product.price,
        shipping_address="123 Test St, Test City"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Add order item
    order_item = models.OrderItem(
        order_id=order.id,
        product_id=test_product.id,
        quantity=1,
        price=test_product.price
    )
    db.add(order_item)
    db.commit()
    
    return order

@pytest.fixture
def test_cart_item(db, normal_user, test_product):
    """Create a test cart item"""
    cart_item = models.CartItem(
        user_id=normal_user.id,
        product_id=test_product.id,
        quantity=1
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


class TestOrderEndpoints:
    """Test order endpoints"""
    
    def test_read_orders_as_admin(self, admin_token, test_order):
        """Test reading all orders as admin"""
        response = client.get(
            "/api/orders/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["shipping_address"] == "123 Test St, Test City"
    
    def test_read_orders_as_user(self, normal_token, test_order):
        """Test reading own orders as regular user"""
        response = client.get(
            "/api/orders/",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["shipping_address"] == "123 Test St, Test City"
    
    def test_read_order_by_id(self, normal_token, test_order):
        """Test reading an order by ID"""
        response = client.get(
            f"/api/orders/{test_order.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["shipping_address"] == "123 Test St, Test City"
        assert data["status"] == "pending"
        assert len(data["items"]) == 1
    
    def test_read_order_not_owner(self, db, admin_token, normal_user, test_product):
        """Test reading an order that doesn't belong to user (non-admin)"""
        # Create an order for admin user
        admin_order = models.Order(
            user_id=db.query(models.User).filter(models.User.is_admin == True).first().id,
            status=models.OrderStatus.PENDING,
            total_amount=test_product.price,
            shipping_address="Admin Address"
        )
        db.add(admin_order)
        db.commit()
        db.refresh(admin_order)
        
        # Try to access as normal user
        response = client.get(
            f"/api/orders/{admin_order.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_create_order(self, normal_token, test_product):
        """Test creating a new order"""
        order_data = {
            "shipping_address": "456 New St, New City",
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 2,
                    "price": test_product.price
                }
            ]
        }
        
        response = client.post(
            "/api/orders/",
            json=order_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["shipping_address"] == "456 New St, New City"
        assert data["status"] == "pending"
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2
    
    def test_update_order_status_as_admin(self, admin_token, test_order):
        """Test updating order status as admin"""
        response = client.put(
            f"/api/orders/{test_order.id}/status",
            params={"status": "processing"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "processing"
    
    def test_update_order_status_as_user(self, normal_token, test_order):
        """Test updating order status as non-admin (should fail)"""
        response = client.put(
            f"/api/orders/{test_order.id}/status",
            params={"status": "processing"},
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 403
    
    def test_cancel_order(self, normal_token, test_order):
        """Test cancelling an order"""
        response = client.post(
            f"/api/orders/{test_order.id}/cancel",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"


class TestCartEndpoints:
    """Test cart endpoints"""
    
    def test_read_cart_items_empty(self, normal_token):
        """Test reading cart items when none exist"""
        response = client.get(
            "/api/orders/cart/items",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_read_cart_items(self, normal_token, test_cart_item):
        """Test reading cart items"""
        response = client.get(
            "/api/orders/cart/items",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["quantity"] == 1
    
    def test_add_to_cart(self, normal_token, test_product):
        """Test adding item to cart"""
        cart_item_data = {
            "product_id": test_product.id,
            "quantity": 2
        }
        
        response = client.post(
            "/api/orders/cart/items",
            json=cart_item_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == test_product.id
        assert data["quantity"] == 2
    
    def test_update_cart_item(self, normal_token, test_cart_item):
        """Test updating cart item quantity"""
        update_data = {
            "quantity": 3
        }
        
        response = client.put(
            f"/api/orders/cart/items/{test_cart_item.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["quantity"] == 3
    
    def test_update_cart_item_not_found(self, normal_token):
        """Test updating non-existent cart item"""
        update_data = {
            "quantity": 3
        }
        
        response = client.put(
            "/api/orders/cart/items/999",
            json=update_data,
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 404
    
    def test_remove_cart_item(self, normal_token, test_cart_item):
        """Test removing item from cart"""
        response = client.delete(
            f"/api/orders/cart/items/{test_cart_item.id}",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        assert response.json() is True
        
        # Verify it's removed
        get_response = client.get(
            "/api/orders/cart/items",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert get_response.json() == []
    
    def test_clear_cart(self, normal_token, test_cart_item):
        """Test clearing the entire cart"""
        # Add another item to verify multiple items get cleared
        client.post(
            "/api/orders/cart/items",
            json={"product_id": test_cart_item.product_id, "quantity": 1},
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        response = client.delete(
            "/api/orders/cart/clear",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        
        assert response.status_code == 200
        # Should return the number of items deleted
        assert response.json() > 0
        
        # Verify cart is empty
        get_response = client.get(
            "/api/orders/cart/items",
            headers={"Authorization": f"Bearer {normal_token}"}
        )
        assert get_response.json() == []