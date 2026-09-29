import uvicorn
from backend.app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} on http://{settings.APP_HOST}:{settings.APP_PORT}")
    print(f"Interactive API Docs: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    print(f"Web Frontend: http://{settings.APP_HOST}:{settings.APP_PORT}/")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level="info"
    )
