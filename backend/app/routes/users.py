from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import User, Post
from ..schemas import UserUpdateRequest, ApiResponse
from ..auth import get_current_user, get_current_admin_user
from ..utils.helpers import format_api_response

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=ApiResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    posts_count = db.query(Post).filter(Post.author_id == current_user.id).count()
    views_total = (
        db.query(func.coalesce(func.sum(Post.views_count), 0))
        .filter(Post.author_id == current_user.id)
        .scalar()
    )

    return format_api_response(
        success=True,
        message="Profile retrieved",
        data={
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "profile_image": current_user.profile_image,
            "bio": current_user.bio,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "posts_count": posts_count,
            "views_count": int(views_total),
        }
    )


@router.put("/me", response_model=ApiResponse)
def update_user_profile(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.name is not None and req.name.strip():
        current_user.name = req.name.strip()

    if req.bio is not None:
        current_user.bio = req.bio.strip() if req.bio else None

    if req.profile_image is not None:
        current_user.profile_image = req.profile_image.strip() if req.profile_image else None

    db.commit()
    db.refresh(current_user)

    posts_count = db.query(Post).filter(Post.author_id == current_user.id).count()

    return format_api_response(
        success=True,
        message="Profile updated successfully",
        data={
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "profile_image": current_user.profile_image,
            "bio": current_user.bio,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "posts_count": posts_count,
        }
    )


@router.get("", response_model=ApiResponse)
def list_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.id.asc()).all()
    user_list = []
    for u in users:
        p_count = db.query(Post).filter(Post.author_id == u.id).count()
        user_list.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "profile_image": u.profile_image,
            "bio": u.bio,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "posts_count": p_count,
        })

    return format_api_response(
        success=True,
        message="Users retrieved successfully",
        data=user_list
    )


@router.patch("/{id}/status", response_model=ApiResponse)
def toggle_user_status(
    id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    if id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own administrative account."
        )

    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    db.commit()

    return format_api_response(
        success=True,
        message=f"User account {'activated' if user.is_active else 'deactivated'} successfully",
        data={"id": user.id, "is_active": user.is_active}
    )


@router.patch("/{id}/role", response_model=ApiResponse)
def change_user_role(
    id: int,
    new_role: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    if id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot modify your own administrative role."
        )

    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role specified")

    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = new_role
    db.commit()

    return format_api_response(
        success=True,
        message=f"User role updated to {new_role}",
        data={"id": user.id, "role": user.role}
    )
