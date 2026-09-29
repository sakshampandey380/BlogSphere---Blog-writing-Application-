from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Tag, post_tags, User
from ..schemas import TagCreate, ApiResponse
from ..auth import get_current_user, get_current_admin_user
from ..utils.helpers import slugify, get_unique_slug, format_api_response

router = APIRouter(prefix="/api/tags", tags=["Tags"])


@router.get("", response_model=ApiResponse)
def list_tags(db: Session = Depends(get_db)):
    subquery = (
        db.query(post_tags.c.tag_id, func.count(post_tags.c.post_id).label("post_count"))
        .group_by(post_tags.c.tag_id)
        .subquery()
    )

    results = (
        db.query(Tag, func.coalesce(subquery.c.post_count, 0).label("posts_count"))
        .outerjoin(subquery, Tag.id == subquery.c.tag_id)
        .order_by(Tag.name.asc())
        .all()
    )

    data = [
        {
            "id": tag.id,
            "name": tag.name,
            "slug": tag.slug,
            "posts_count": int(count)
        }
        for tag, count in results
    ]

    return format_api_response(
        success=True,
        message="Tags retrieved successfully",
        data=data
    )


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    req: TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    name_clean = req.name.strip()
    existing = db.query(Tag).filter(Tag.name == name_clean).first()
    if existing:
        return format_api_response(
            success=True,
            message="Tag already exists",
            data={"id": existing.id, "name": existing.name, "slug": existing.slug}
        )

    base_slug = slugify(req.slug if req.slug else name_clean)
    final_slug = get_unique_slug(db, Tag, base_slug)

    tag = Tag(name=name_clean, slug=final_slug)
    db.add(tag)
    db.commit()
    db.refresh(tag)

    return format_api_response(
        success=True,
        message="Tag created successfully",
        data={"id": tag.id, "name": tag.name, "slug": tag.slug}
    )


@router.delete("/{id}", response_model=ApiResponse)
def delete_tag(
    id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    tag = db.query(Tag).filter(Tag.id == id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()

    return format_api_response(
        success=True,
        message="Tag deleted successfully",
        data={}
    )
