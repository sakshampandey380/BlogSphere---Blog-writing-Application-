from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserSettings, Post
from ..schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    ApiResponse,
)
from ..utils.security import hash_password, verify_password, create_access_token
from ..utils.helpers import format_api_response
from ..auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    hashed_pw = hash_password(req.password)
    user_count = db.query(User).count()
    assigned_role = "admin" if user_count == 0 else (req.role if req.role in ["user", "admin"] else "user")

    new_user = User(
        name=req.name.strip(),
        email=req.email.lower().strip(),
        password_hash=hashed_pw,
        role=assigned_role,
        is_active=True,
        last_login=datetime.utcnow()
    )
    db.add(new_user)
    db.flush()

    settings = UserSettings(
        user_id=new_user.id,
        theme="light",
        email_notifications=True,
        comment_notifications=True,
        post_visibility="public"
    )
    db.add(settings)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(subject=str(new_user.id))

    user_data = {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "profile_image": new_user.profile_image,
        "bio": new_user.bio,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at.isoformat(),
        "posts_count": 0
    }

    return format_api_response(
        success=True,
        message="Account created successfully",
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": user_data
        }
    )


@router.post("/login", response_model=ApiResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact an administrator."
        )

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(subject=str(user.id))
    posts_count = db.query(Post).filter(Post.author_id == user.id).count()

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "profile_image": user.profile_image,
        "bio": user.bio,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "posts_count": posts_count
    }

    return format_api_response(
        success=True,
        message="Login successful",
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": user_data
        }
    )


@router.post("/logout", response_model=ApiResponse)
def logout_user():
    return format_api_response(
        success=True,
        message="Logged out successfully",
        data={}
    )


@router.get("/me", response_model=ApiResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts_count = db.query(Post).filter(Post.author_id == current_user.id).count()
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    return format_api_response(
        success=True,
        message="User profile retrieved",
        data={
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "role": current_user.role,
                "profile_image": current_user.profile_image,
                "bio": current_user.bio,
                "is_active": current_user.is_active,
                "created_at": current_user.created_at.isoformat(),
                "posts_count": posts_count
            },
            "settings": {
                "theme": settings.theme if settings else "light",
                "email_notifications": settings.email_notifications if settings else True,
                "comment_notifications": settings.comment_notifications if settings else True,
                "post_visibility": settings.post_visibility if settings else "public"
            } if settings else None
        }
    )
