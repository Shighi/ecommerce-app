from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import schemas
from app.db.database import get_db
from app.services import user_service
from app.utils.helpers import get_current_user, get_admin_user, oauth2_scheme

router = APIRouter()


@router.get("/me", response_model=schemas.User)
def read_users_me(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Get current user profile"""
    current_user = get_current_user(token=token, db=db)
    return current_user


@router.put("/me", response_model=schemas.User)
def update_users_me(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Update current user profile"""
    current_user = get_current_user(token=token, db=db)
    updated_user = user_service.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user",
        )
    return updated_user


@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Get list of users (admin only)"""
    get_admin_user(token=token, db=db)
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Get user by ID (admin only)"""
    get_admin_user(token=token, db=db)
    db_user = user_service.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Update user by ID (admin only)"""
    get_admin_user(token=token, db=db)
    updated_user = user_service.update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/{user_id}", response_model=bool)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """Delete user by ID (admin only)"""
    get_admin_user(token=token, db=db)
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return True