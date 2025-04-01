from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import models, schemas
from app.db.database import get_db
from app.services import order_service
from app.utils.helpers import get_current_user, get_admin_user, oauth2_scheme

router = APIRouter()


# Order endpoints
@router.get("/", response_model=List[schemas.Order])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Get all orders (admin only) or current user's orders"""
    current_user = get_current_user(token=token, db=db)
    
    if current_user.is_admin:
        orders = order_service.get_all_orders(db, skip=skip, limit=limit)
    else:
        orders = order_service.get_orders_by_user(
            db, user_id=current_user.id, skip=skip, limit=limit
        )
    
    return orders


@router.get("/{order_id}", response_model=schemas.Order)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Get order by ID (admin or order owner only)"""
    current_user = get_current_user(token=token, db=db)
    order = order_service.get_order_by_id(db, order_id=order_id)
    
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order",
        )
    
    return order


@router.post("/", response_model=schemas.Order)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Create a new order for the current user"""
    current_user = get_current_user(token=token, db=db)
    db_order = order_service.create_order(db=db, order=order, user_id=current_user.id)
    
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create order. Check product availability.",
        )
    
    return db_order


@router.put("/{order_id}/status", response_model=schemas.Order)
def update_order_status(
    order_id: int,
    status: models.OrderStatus,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Update order status (admin only)"""
    get_admin_user(token=token, db=db)
    updated_order = order_service.update_order_status(db, order_id, status)
    
    if updated_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return updated_order


@router.post("/{order_id}/cancel", response_model=schemas.Order)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Cancel an order (admin or order owner only)"""
    current_user = get_current_user(token=token, db=db)
    order = order_service.get_order_by_id(db, order_id=order_id)
    
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check permissions
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this order",
        )
    
    cancelled_order = order_service.cancel_order(db, order_id)
    
    if cancelled_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel order in current status",
        )
    
    return cancelled_order


# Cart endpoints
@router.get("/cart/items", response_model=List[schemas.CartItem])
def read_cart_items(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Get current user's cart items"""
    current_user = get_current_user(token=token, db=db)
    return order_service.get_cart_items(db, user_id=current_user.id)


@router.post("/cart/items", response_model=schemas.CartItem)
def add_cart_item(
    item: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Add item to current user's cart"""
    current_user = get_current_user(token=token, db=db)
    db_item, _ = order_service.add_to_cart(db, current_user.id, item)
    
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add item to cart. Check product availability.",
        )
    
    return db_item


@router.put("/cart/items/{item_id}", response_model=schemas.CartItem)
def update_cart_item(
    item_id: int,
    update: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Update quantity of an item in current user's cart"""
    current_user = get_current_user(token=token, db=db)
    updated_item = order_service.update_cart_item(
        db, current_user.id, item_id, update.quantity
    )
    
    if updated_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found or insufficient stock",
        )
    
    return updated_item


@router.delete("/cart/items/{item_id}", response_model=bool)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Remove item from current user's cart"""
    current_user = get_current_user(token=token, db=db)
    success = order_service.remove_from_cart(db, current_user.id, item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )
    
    return True


@router.delete("/cart/clear", response_model=int)
def clear_cart(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Clear all items from current user's cart"""
    current_user = get_current_user(token=token, db=db)
    deleted_count = order_service.clear_cart(db, current_user.id)
    return deleted_count