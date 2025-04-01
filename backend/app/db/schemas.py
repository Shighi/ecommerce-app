from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryInDBBase(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Category(CategoryInDBBase):
    pass


# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    image_url: Optional[str] = None
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductInDBBase(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Product(ProductInDBBase):
    pass


# OrderItem schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemInDBBase(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class OrderItem(OrderItemInDBBase):
    product: Product


# Order schemas
class OrderBase(BaseModel):
    shipping_address: str
    status: OrderStatus = OrderStatus.PENDING


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    shipping_address: Optional[str] = None
    status: Optional[OrderStatus] = None


class OrderInDBBase(OrderBase):
    id: int
    user_id: int
    total_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Order(OrderInDBBase):
    items: List[OrderItem] = []


# CartItem schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemInDBBase(CartItemBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CartItem(CartItemInDBBase):
    product: Product


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None