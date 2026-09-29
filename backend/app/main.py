import os
from pathlib import Path
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routes import (
    auth,
    posts,
    categories,
    tags,
    users,
    dashboard,
    comments,
)
from .utils.helpers import format_api_response

app = FastAPI(
    title="BlogSphere API",
    version=settings.APP_VERSION,
    description="A modern, high-performance publishing platform & CMS API built with FastAPI and MySQL.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=format_api_response(
            success=False,
            message=str(exc.detail),
            data=None,
            errors=getattr(exc, "errors", None)
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        error_details.append(f"{field}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_api_response(
            success=False,
            message="Validation error: " + "; ".join(error_details[:3]),
            data=None,
            errors=exc.errors(),
        ),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_api_response(
            success=False,
            message="An unexpected server error occurred. Please try again later.",
            data=None,
            errors=str(exc) if settings.APP_DEBUG else None
        ),
    )


@app.get("/api/health", tags=["Health"])
def health_check():
    return format_api_response(
        success=True,
        message="BlogSphere API is running smoothly",
        data={"version": settings.APP_VERSION, "status": "healthy"}
    )


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(comments.router)
app.include_router(comments.comments_admin_router)

# Mount Frontend directory
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
