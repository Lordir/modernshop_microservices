from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import time
import jwt
from datetime import datetime, timedelta

app = FastAPI(title="Auth Service")

# Мок база данных пользователей (временная)
fake_users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "password": "password123",
        "is_active": True
    }
}


# Модели
class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    email: str
    is_active: bool
    access_token: Optional[str] = None


# Секретный ключ (в продакшене хранить в env)
SECRET_KEY = "your-secret-key-for-testing"
ALGORITHM = "HS256"


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": time.time()
    }


@app.post("/auth/login")
async def login(user_data: UserLogin):
    # Проверяем существование пользователя
    user = fake_users_db.get(user_data.email)

    if not user or user["password"] != user_data.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # Создаем JWT токен
    token_data = {
        "sub": user_data.email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return UserResponse(
        email=user_data.email,
        is_active=user["is_active"],
        access_token=access_token
    )


@app.post("/auth/register")
async def register(user_data: UserLogin):
    if user_data.email in fake_users_db:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # Сохраняем пользователя
    fake_users_db[user_data.email] = {
        "email": user_data.email,
        "password": user_data.password,
        "is_active": True
    }

    return {
        "message": "User registered successfully",
        "email": user_data.email
    }


@app.get("/auth/me")
async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email not in fake_users_db:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = fake_users_db[email]
        return UserResponse(
            email=user["email"],
            is_active=user["is_active"]
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )