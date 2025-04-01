from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models
from app.core.security import get_password_hash

def init_db():
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin = db.query(models.User).filter(models.User.email == "admin@example.com").first()
        if not admin:
            # Create admin user
            admin = models.User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("Admin user created")
        
        # Create categories
        categories = [
            {"name": "Electronics", "description": "Electronic devices and accessories"},
            {"name": "Clothing", "description": "Clothes, shoes and accessories"},
            {"name": "Books", "description": "Books, e-books and audiobooks"},
            {"name": "Home", "description": "Furniture and home decor"},
            {"name": "Sports", "description": "Sports equipment and accessories"}
        ]
        
        for cat_data in categories:
            cat = db.query(models.Category).filter(models.Category.name == cat_data["name"]).first()
            if not cat:
                cat = models.Category(**cat_data)
                db.add(cat)
                db.commit()
        
        # Get category IDs
        electronics = db.query(models.Category).filter(models.Category.name == "Electronics").first()
        clothing = db.query(models.Category).filter(models.Category.name == "Clothing").first()
        books = db.query(models.Category).filter(models.Category.name == "Books").first()
        
        # Create sample products
        products = [
            {
                "name": "Smartphone", 
                "description": "Latest smartphone model with high-end features", 
                "price": 699.99, 
                "stock": 50, 
                "image_url": "https://via.placeholder.com/300", 
                "category_id": electronics.id
            },
            {
                "name": "Laptop", 
                "description": "Powerful laptop for work and gaming", 
                "price": 1299.99, 
                "stock": 30, 
                "image_url": "https://via.placeholder.com/300", 
                "category_id": electronics.id
            },
            {
                "name": "T-Shirt", 
                "description": "Comfortable cotton t-shirt", 
                "price": 19.99, 
                "stock": 100, 
                "image_url": "https://via.placeholder.com/300", 
                "category_id": clothing.id
            },
            {
                "name": "Jeans", 
                "description": "Classic blue jeans", 
                "price": 49.99, 
                "stock": 80, 
                "image_url": "https://via.placeholder.com/300", 
                "category_id": clothing.id
            },
            {
                "name": "Python Programming", 
                "description": "Comprehensive guide to Python programming", 
                "price": 39.99, 
                "stock": 60, 
                "image_url": "https://via.placeholder.com/300", 
                "category_id": books.id
            }
        ]
        
        for prod_data in products:
            prod = db.query(models.Product).filter(models.Product.name == prod_data["name"]).first()
            if not prod:
                prod = models.Product(**prod_data)
                db.add(prod)
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
        
        print("Database initialized with sample data")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()