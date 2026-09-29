from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Category, Post, User
from ..schemas import CategoryCreate, CategoryUpdate, ApiResponse
from ..auth import get_current_admin_user
from ..utils.helpers import slugify, get_unique_slug, format_api_response

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=ApiResponse)
def list_categories(db: Session = Depends(get_db)):
    subquery = (
        db.query(Post.category_id, func.count(Post.id).label("post_count"))
        .filter(Post.status == "published")
        .group_by(Post.category_id)
        .subquery()
    )

    results = (
        db.query(Category, func.coalesce(subquery.c.post_count, 0).label("posts_count"))
        .outerjoin(subquery, Category.id == subquery.c.category_id)
        .order_by(Category.name.asc())
        .all()
    )

    data = [
        {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "created_at": cat.created_at.isoformat() if cat.created_at else None,
            "posts_count": int(count),
        }
        for cat, count in results
    ]

    return format_api_response(
        success=True,
        message="Categories retrieved successfully",
        data=data
    )


@router.get("/{id}", response_model=ApiResponse)
def get_category(id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    count = db.query(Post).filter(Post.category_id == id, Post.status == "published").count()
    return format_api_response(
        success=True,
        message="Category retrieved",
        data={
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "posts_count": count
        }
    )


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    req: CategoryCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Category).filter(Category.name == req.name.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )

    base_slug = slugify(req.slug if req.slug else req.name)
    final_slug = get_unique_slug(db, Category, base_slug)

    category = Category(
        name=req.name.strip(),
        slug=final_slug,
        description=req.description.strip() if req.description else None,
        created_by=current_user.id
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return format_api_response(
        success=True,
        message="Category created successfully",
        data={
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "posts_count": 0
        }
    )


@router.put("/{id}", response_model=ApiResponse)
def update_category(
    id: int,
    req: CategoryUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if req.name is not None:
        name_clean = req.name.strip()
        existing = db.query(Category).filter(Category.name == name_clean, Category.id != id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Another category has this name")
        category.name = name_clean

        if req.slug:
            category.slug = get_unique_slug(db, Category, slugify(req.slug), current_id=id)
        elif not category.slug:
            category.slug = get_unique_slug(db, Category, slugify(name_clean), current_id=id)

    if req.description is not None:
        category.description = req.description.strip() if req.description else None

    db.commit()
    db.refresh(category)

    return format_api_response(
        success=True,
        message="Category updated successfully",
        data={
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "posts_count": db.query(Post).filter(Post.category_id == id).count()
        }
    )


@router.delete("/{id}", response_model=ApiResponse)
def delete_category(
    id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.query(Post).filter(Post.category_id == id).update({"category_id": None})
    db.delete(category)
    db.commit()

    return format_api_response(
        success=True,
        message="Category deleted successfully",
        data={}
    )
