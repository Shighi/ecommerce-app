from typing import List, Optional

from sqlalchemy.orm import Session

from app.db import models, schemas


def get_product_by_id(db: Session, product_id: int) -> Optional[models.Product]:
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(
    db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None
) -> List[models.Product]:
    query = db.query(models.Product)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    return query.offset(skip).limit(limit).all()


def search_products(db: Session, query: str, limit: int = 100) -> List[models.Product]:
    return (
        db.query(models.Product)
        .filter(models.Product.name.ilike(f"%{query}%"))
        .limit(limit)
        .all()
    )


def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(
    db: Session, product_id: int, product_data: schemas.ProductUpdate
) -> Optional[models.Product]:
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        return None
    
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        return False
    
    db.delete(db_product)
    db.commit()
    return True


def get_category_by_id(db: Session, category_id: int) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[models.Category]:
    return db.query(models.Category).offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(
    db: Session, category_id: int, category_data: schemas.CategoryUpdate
) -> Optional[models.Category]:
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return None
    
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> bool:
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return False
    
    db.delete(db_category)
    db.commit()
    return True