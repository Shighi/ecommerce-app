# E-commerce Backend API

A fully-featured RESTful API for e-commerce applications built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- **Authentication & Authorization**
  - JWT-based authentication
  - Role-based access control (admin vs regular users)
  - Secure password hashing with bcrypt

- **User Management**
  - User registration and authentication
  - Profile management
  - Admin capabilities for user management

- **Product Management**
  - Product CRUD operations
  - Category organization
  - Search and filtering capabilities

- **Shopping Experience**
  - Shopping cart functionality
  - Order processing
  - Order status updates and tracking

- **Database**
  - PostgreSQL integration
  - Data schema with proper relationships
  - Database migration support with Alembic

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation and settings management
- **PostgreSQL** - Robust relational database
- **JWT** - Secure authentication
- **Docker** - Containerization for easy deployment
- **pytest** - Comprehensive testing suite

## Project Structure

```
ecommerce-backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core configuration
│   ├── db/               # Database models and schemas
│   ├── services/         # Business logic
│   ├── utils/            # Utility functions
│   └── __init__.py
├── tests/                # Test suite
├── docker-compose.yml    # Docker composition
├── main.py               # Application entry point
├── init_db.py            # Database initialization
├── requirements.txt      # Dependencies
└── README.md             # Documentation
```

## API Endpoints

### Authentication

- `POST /login` - Authenticate user and receive JWT token
- `POST /register` - Register a new user
- `POST /test-token` - Validate authentication token

### Users

- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `GET /users/` - Get all users (admin only)
- `GET /users/{user_id}` - Get user by ID (admin only)
- `PUT /users/{user_id}` - Update user by ID (admin only)
- `DELETE /users/{user_id}` - Delete user by ID (admin only)

### Products

- `GET /products/` - Get all products with optional filtering
- `GET /products/{product_id}` - Get product by ID
- `POST /products/` - Create new product (admin only)
- `PUT /products/{product_id}` - Update product (admin only)
- `DELETE /products/{product_id}` - Delete product (admin only)

### Categories

- `GET /products/categories/` - Get all categories
- `GET /products/categories/{category_id}` - Get category by ID
- `POST /products/categories/` - Create new category (admin only)
- `PUT /products/categories/{category_id}` - Update category (admin only)
- `DELETE /products/categories/{category_id}` - Delete category (admin only)

### Cart

- `GET /cart/items` - Get all items in user's cart
- `POST /cart/items` - Add item to cart
- `PUT /cart/items/{item_id}` - Update cart item quantity
- `DELETE /cart/items/{item_id}` - Remove item from cart
- `DELETE /cart/clear` - Clear cart

### Orders

- `GET /orders/` - Get user orders (or all orders for admin)
- `GET /orders/{order_id}` - Get order by ID
- `POST /orders/` - Create a new order
- `PUT /orders/{order_id}/status` - Update order status (admin only)
- `POST /orders/{order_id}/cancel` - Cancel an order

## Installation & Setup

### Using Docker

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ecommerce-app.git
   cd ecommerce-app
   cd backend
   ```

2. Create a `.env` file with the following variables:
   ```
   DATABASE_URL=postgresql://postgres:password@db:5432/ecommerce
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. Build and run with Docker Compose:
   ```
   docker-compose up --build
   ```

4. The API will be available at http://localhost:8000

### Local Development

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ecommerce-backend.git
   cd ecommerce-backend
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your `.env` file with your database connection and security settings.

5. Initialize the database:
   ```
   python init_db.py
   ```

6. Run the application:
   ```
   uvicorn main:app --reload
   ```

## Testing

Run the test suite with:
```
pytest
```

## API Documentation

When the application is running, you can access:
- Swagger UI documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.