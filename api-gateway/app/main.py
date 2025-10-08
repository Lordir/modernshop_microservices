from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ModernShop API Gateway",
    description="Единая точка входа для всех микросервисов",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация сервисов
SERVICE_CONFIG = {
    "auth": "http://auth-service:8001",
    "catalog": "http://catalog-service:8002",
}


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": time.time()
    }


# Главная страница
@app.get("/")
async def root():
    return {
        "message": "Welcome to ModernShop API Gateway",
        "docs": "/docs",
        "health": "/health"
    }


# Прокси для auth service
@app.post("/auth/{path:path}")
async def auth_proxy(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        try:
            # Получаем тело запроса
            body = await request.json()

            # Проксируем запрос в auth service
            response = await client.post(
                f"{SERVICE_CONFIG['auth']}/auth/{path}",
                json=body,
                timeout=30.0
            )

            logger.info(f"Auth service response: {response.status_code}")
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is unavailable"
            )
        except Exception as e:
            logger.error(f"Error proxying to auth service: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )


# Прокси для catalog service
@app.get("/catalog/{path:path}")
async def catalog_proxy(path: str, request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SERVICE_CONFIG['catalog']}/catalog/{path}",
                params=dict(request.query_params),
                timeout=30.0
            )

            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Catalog service is unavailable"
            )


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"Method: {request.method} "
        f"Path: {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {process_time:.2f}s"
    )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоперезагрузка для разработки
        log_level="info"
    )