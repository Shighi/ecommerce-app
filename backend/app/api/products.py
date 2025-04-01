from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import schemas
from app.db.database import get_db
from app.services import product_service
from app.utils.helpers import get_admin_user, oauth2_scheme

router = APIRouter()

# Product endpoints
@router.get("/", response_model=List[schemas.Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get list of products with optional filtering"""
    if search:
        products = product_service.search_products(db, query=search, limit=limit)
    else:
        products = product_service.get_products(
            db, skip=skip, limit=limit, category_id=category_id
        )
    return products


@router.get("/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    db_product = product_service.get_product_by_id(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@router.post("/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Create a new product (admin only)"""
    get_admin_user(token=token, db=db)
    # Verify category exists
    db_category = product_service.get_category_by_id(db, product.category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )
    return product_service.create_product(db=db, product=product)


@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Update product by ID (admin only)"""
    get_admin_user(token=token, db=db)
    # Verify category exists if provided
    if product.category_id is not None:
        db_category = product_service.get_category_by_id(db, product.category_id)
        if not db_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
    
    updated_product = product_service.update_product(db, product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product


@router.delete("/{product_id}", response_model=bool)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Delete product by ID (admin only)"""
    get_admin_user(token=token, db=db)
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return True


# Category endpoints
@router.get("/categories/", response_model=List[schemas.Category])
def read_categories(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Get list of categories"""
    categories = product_service.get_categories(db, skip=skip, limit=limit)
    return categories


@router.get("/categories/{category_id}", response_model=schemas.Category)
def read_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID"""
    db_category = product_service.get_category_by_id(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.post("/categories/", response_model=schemas.Category)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Create a new category (admin only)"""
    get_admin_user(token=token, db=db)
    return product_service.create_category(db=db, category=category)


@router.put("/categories/{category_id}", response_model=schemas.Category)
def update_category(
    category_id: int,
    category: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Update category by ID (admin only)"""
    get_admin_user(token=token, db=db)
    updated_category = product_service.update_category(db, category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category


@router.delete("/categories/{category_id}", response_model=bool)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Delete category by ID (admin only)"""
    get_admin_user(token=token, db=db)
    success = product_service.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return True