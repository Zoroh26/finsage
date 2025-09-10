# FinSage - AI Personal Finance Assistant

An AI-powered personal finance assistant that consolidates financial data from multiple sources and provides intelligent, conversational financial insights and recommendations.

## 🚀 Features

- **User Authentication & Onboarding**: Secure email/password registration and login with JWT tokens
- **Database Integration**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **RESTful API**: FastAPI-based backend with automatic API documentation
- **Security**: Password hashing with bcrypt and JWT token authentication

## 📋 Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher
- Git

## 🛠️ Installation Guide

### 1. Clone the repository
```bash
git clone https://github.com/Zoroh26/finsage.git
cd finsage
```

### 2. Create a virtual environment
```bash
python -m venv venv
```

### 3. Activate the virtual environment
- **Windows (PowerShell):**
  ```bash
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (cmd):**
  ```bash
  venv\Scripts\activate.bat
  ```
- **Linux/macOS:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. PostgreSQL Setup
1. Install PostgreSQL and create a database named `finsage`
2. Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/finsage
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```
   Replace `username` and `password` with your PostgreSQL credentials.

### 6. Database Migration
```bash
# Generate migration files
alembic revision --autogenerate -m "create users table"

# Apply migrations
alembic upgrade head
```

### 7. Run the FastAPI server
```bash
uvicorn main:app --reload
```

### 8. Access the API
Open your browser and go to:
- [http://127.0.0.1:8000](http://127.0.0.1:8000) — Main API
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — Interactive Swagger UI
- [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) — ReDoc API Documentation

## 📁 Project Structure
```
finsage/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
├── alembic.ini           # Alembic configuration
├── alembic/              # Database migrations
│   ├── env.py
│   └── versions/
├── controllers/          # Route handlers
│   └── auth.py
├── core/                 # Core functionality
│   └── database.py
├── models/               # Database models and schemas
│   ├── user.py
│   └── schemas.py
├── routes/               # Route definitions
│   └── auth.py
├── services/             # Business logic
│   └── auth.py
└── utils/                # Utility functions
    └── jwt.py
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token

## 🧪 Testing

### Test User Registration
```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword",
       "name": "Test User",
       "age": 25,
       "income": 50000,
       "risk_tolerance": "medium"
     }'
```

### Test User Login
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword"
     }'
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error:**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in `.env` file
   - Ensure database `finsage` exists

2. **Migration Errors:**
   - Delete migration files in `alembic/versions/` and regenerate
   - Clear `alembic_version` table and run `alembic stamp head`

3. **Import Errors:**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

4. **Password with Special Characters:**
   - URL-encode special characters in DATABASE_URL (e.g., `@` becomes `%40`)

## 🛣️ Roadmap

- [ ] Fi MCP Integration
- [ ] Financial Dashboard
- [ ] AI Chat Interface (Gemini Pro)
- [ ] Investment Tracking
- [ ] Goal Setting & Tracking
- [ ] Financial Analytics

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
services/
utills/
```

---

## Troubleshooting
- If `uvicorn` is not recognized, ensure your virtual environment is activated and run `pip install uvicorn fastapi`.
- For additional dependencies, add them to `requirements.txt` and run `pip install -r requirements.txt` again.

---

## License
MIT
