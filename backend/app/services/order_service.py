from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db import models, schemas
from app.services import product_service


def get_order_by_id(db: Session, order_id: int) -> Optional[models.Order]:
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_orders_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[models.Order]:
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_orders(db: Session, skip: int = 0, limit: int = 100) -> List[models.Order]:
    return db.query(models.Order).offset(skip).limit(limit).all()


def create_order(
    db: Session, order: schemas.OrderCreate, user_id: int
) -> Optional[models.Order]:
    # Calculate total amount and ensure products have sufficient stock
    total_amount = 0
    order_items_data = []
    
    for item in order.items:
        product = product_service.get_product_by_id(db, item.product_id)
        if not product:
            return None  # Product not found
        
        if product.stock < item.quantity:
            return None  # Insufficient stock
        
        # Update product stock
        product.stock -= item.quantity
        
        # Store item data for later use
        item_total = item.price * item.quantity
        total_amount += item_total
        order_items_data.append(
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price,
            }
        )
    
    # Create the order
    db_order = models.Order(
        user_id=user_id,
        status=models.OrderStatus.PENDING,
        total_amount=total_amount,
        shipping_address=order.shipping_address,
    )
    db.add(db_order)
    db.flush()  # Flush to get the order ID
    
    # Create order items
    for item_data in order_items_data:
        db_item = models.OrderItem(order_id=db_order.id, **item_data)
        db.add(db_item)
    
    # Clear the user's cart
    db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()
    
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order_status(
    db: Session, order_id: int, status: models.OrderStatus
) -> Optional[models.Order]:
    db_order = get_order_by_id(db, order_id)
    if not db_order:
        return None
    
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order


def cancel_order(db: Session, order_id: int) -> Optional[models.Order]:
    db_order = get_order_by_id(db, order_id)
    if not db_order:
        return None
    
    # Only allow cancellation if order is pending or processing
    if db_order.status not in [models.OrderStatus.PENDING, models.OrderStatus.PROCESSING]:
        return None
    
    # Return items to inventory
    for item in db_order.items:
        product = product_service.get_product_by_id(db, item.product_id)
        if product:
            product.stock += item.quantity
    
    db_order.status = models.OrderStatus.CANCELLED
    db.commit()
    db.refresh(db_order)
    return db_order


def get_cart_items(db: Session, user_id: int) -> List[models.CartItem]:
    return db.query(models.CartItem).filter(models.CartItem.user_id == user_id).all()


def add_to_cart(
    db: Session, user_id: int, item: schemas.CartItemCreate
) -> Tuple[models.CartItem, bool]:
    # Check if product exists and has enough stock
    product = product_service.get_product_by_id(db, item.product_id)
    if not product:
        return None, False
    
    if product.stock < item.quantity:
        return None, False
    
    # Check if item already in cart
    existing_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.user_id == user_id,
            models.CartItem.product_id == item.product_id,
        )
        .first()
    )
    
    created = False
    if existing_item:
        existing_item.quantity += item.quantity
        db_item = existing_item
    else:
        db_item = models.CartItem(user_id=user_id, **item.dict())
        db.add(db_item)
        created = True
    
    db.commit()
    db.refresh(db_item)
    return db_item, created


def update_cart_item(
    db: Session, user_id: int, item_id: int, quantity: int
) -> Optional[models.CartItem]:
    db_item = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.id == item_id, models.CartItem.user_id == user_id
        )
        .first()
    )
    
    if not db_item:
        return None
    
    # Check stock
    product = product_service.get_product_by_id(db, db_item.product_id)
    if product.stock < quantity:
        return None
    
    db_item.quantity = quantity
    db.commit()
    db.refresh(db_item)
    return db_item


def remove_from_cart(db: Session, user_id: int, item_id: int) -> bool:
    deleted = (
        db.query(models.CartItem)
        .filter(
            models.CartItem.id == item_id, models.CartItem.user_id == user_id
        )
        .delete()
    )
    db.commit()
    return deleted > 0


def clear_cart(db: Session, user_id: int) -> int:
    deleted = db.query(models.CartItem).filter(models.CartItem.user_id == user_id).delete()
    db.commit()
    return deleted