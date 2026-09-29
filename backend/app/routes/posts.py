from datetime import datetime
from typing import Optional, List
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, func, select

from ..database import get_db
from ..models import Post, User, Category, Tag, post_tags, PostView, Comment
from ..schemas import PostCreate, PostUpdate, ApiResponse
from ..auth import get_current_user, get_optional_user
from ..utils.sanitizer import sanitize_html
from ..utils.helpers import (
    slugify,
    get_unique_slug,
    calculate_reading_time,
    format_api_response,
)

router = APIRouter(prefix="/api/posts", tags=["Posts"])


def serialize_user(user: Optional[User]) -> Optional[dict]:
    if not user:
        return None
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "profile_image": user.profile_image,
        "bio": user.bio,
    }


def serialize_category(category: Optional[Category]) -> Optional[dict]:
    if not category:
        return None
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
    }


def serialize_tag(tag: Tag) -> dict:
    return {
        "id": tag.id,
        "name": tag.name,
        "slug": tag.slug,
    }


def serialize_post(post: Post, include_content: bool = False, db: Optional[Session] = None) -> dict:
    data = {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt,
        "featured_image": post.featured_image,
        "status": post.status,
        "is_featured": bool(post.is_featured),
        "views_count": int(post.views_count or 0),
        "reading_time_minutes": int(post.reading_time_minutes or 1),
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "author": serialize_user(post.author),
        "category": serialize_category(post.category),
        "tags": [serialize_tag(t) for t in post.tags],
    }
    if include_content:
        data["content"] = post.content
        if db:
            comments_count = (
                db.query(Comment)
                .filter(Comment.post_id == post.id, Comment.status == "approved")
                .count()
            )
            data["comments_count"] = comments_count
        else:
            data["comments_count"] = len(post.comments) if post.comments else 0
    return data


def sync_post_tags(db: Session, post: Post, tag_names: List[str]):
    cleaned_names = [t.strip() for t in tag_names if t and t.strip()]
    if not cleaned_names:
        post.tags = []
        return

    tags_to_attach = []
    for name in cleaned_names:
        tag = db.query(Tag).filter(func.lower(Tag.name) == func.lower(name)).first()
        if not tag:
            tag_slug = get_unique_slug(db, Tag, slugify(name))
            tag = Tag(name=name, slug=tag_slug)
            db.add(tag)
            db.flush()
        tags_to_attach.append(tag)

    post.tags = tags_to_attach


@router.get("", response_model=ApiResponse)
def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(9, ge=1, le=50),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    author_id: Optional[int] = Query(None),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.tags),
        )
    )

    is_admin = current_user and current_user.role == "admin"
    if status and current_user:
        if is_admin:
            if status != "all":
                query = query.filter(Post.status == status)
        else:
            if status == "draft":
                query = query.filter(Post.status == "draft", Post.author_id == current_user.id)
            elif status != "all":
                query = query.filter(
                    or_(
                        Post.status == "published",
                        and_(Post.status == status, Post.author_id == current_user.id),
                    )
                )
    else:
        query = query.filter(Post.status == "published")

    if author_id:
        query = query.filter(Post.author_id == author_id)

    if featured is not None:
        query = query.filter(Post.is_featured == (1 if featured else 0))

    if category:
        category_clean = category.strip()
        if category_clean.isdigit():
            query = query.filter(Post.category_id == int(category_clean))
        else:
            query = query.join(Post.category).filter(
                or_(Category.slug == category_clean, Category.name == category_clean)
            )

    if tag:
        tag_clean = tag.strip().lower()
        query = query.join(Post.tags).filter(
            or_(func.lower(Tag.slug) == tag_clean, func.lower(Tag.name) == tag_clean)
        )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Post.title.ilike(s),
                Post.excerpt.ilike(s),
                Post.content.ilike(s),
                Post.tags.any(Tag.name.ilike(s)),
            )
        )

    total = query.distinct().count()

    query = query.order_by(
        desc(Post.is_featured),
        desc(func.coalesce(Post.published_at, Post.created_at))
    )

    offset = (page - 1) * limit
    posts = query.offset(offset).limit(limit).all()

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    items = [serialize_post(p, include_content=False, db=db) for p in posts]

    return format_api_response(
        success=True,
        message="Posts retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        },
    )


@router.get("/slug/{slug}", response_model=ApiResponse)
def get_post_by_slug(
    slug: str,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.tags),
        )
        .filter(Post.slug == slug.strip())
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested article does not exist or may have been removed.",
        )

    is_admin = current_user and current_user.role == "admin"
    is_author = current_user and current_user.id == post.author_id
    if post.status != "published" and not (is_admin or is_author):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This article is currently in draft mode and not publicly available.",
        )

    if post.status == "published":
        try:
            client_ip = request.client.host if request.client else "127.0.0.1"
            user_agent = request.headers.get("user-agent", "")[:500]
            ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
            visitor_id = request.cookies.get("blogsphere_visitor_id") or ip_hash

            existing_view = (
                db.query(PostView)
                .filter(
                    PostView.post_id == post.id,
                    or_(
                        and_(PostView.user_id != None, PostView.user_id == (current_user.id if current_user else None)),
                        PostView.ip_hash == ip_hash,
                        PostView.visitor_identifier == visitor_id,
                    ),
                )
                .first()
            )

            if not existing_view:
                new_view = PostView(
                    post_id=post.id,
                    user_id=current_user.id if current_user else None,
                    visitor_identifier=visitor_id,
                    ip_hash=ip_hash,
                    user_agent=user_agent,
                )
                db.add(new_view)
                post.views_count = (post.views_count or 0) + 1
                db.commit()
        except Exception:
            db.rollback()

    return format_api_response(
        success=True,
        message="Post retrieved successfully",
        data=serialize_post(post, include_content=True, db=db),
    )


@router.get("/{id}", response_model=ApiResponse)
def get_post_by_id(
    id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.tags),
        )
        .filter(Post.id == id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    is_admin = current_user and current_user.role == "admin"
    is_author = current_user and current_user.id == post.author_id
    if post.status != "published" and not (is_admin or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this unpublished article.",
        )

    return format_api_response(
        success=True,
        message="Post retrieved successfully",
        data=serialize_post(post, include_content=True, db=db),
    )


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    req: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.category_id:
        cat = db.query(Category).filter(Category.id == req.category_id).first()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {req.category_id} does not exist.",
            )

    clean_content = sanitize_html(req.content)
    reading_time = calculate_reading_time(clean_content)

    base_slug = slugify(req.slug if req.slug else req.title)
    final_slug = get_unique_slug(db, Post, base_slug)

    pub_at = req.published_at
    if req.status == "published" and not pub_at:
        pub_at = datetime.utcnow()

    post = Post(
        author_id=current_user.id,
        category_id=req.category_id,
        title=req.title.strip(),
        slug=final_slug,
        excerpt=req.excerpt.strip() if req.excerpt else None,
        content=clean_content,
        featured_image=req.featured_image.strip() if req.featured_image else None,
        status=req.status if req.status in ["draft", "published", "archived"] else "draft",
        is_featured=bool(req.is_featured),
        reading_time_minutes=reading_time,
        published_at=pub_at,
    )

    db.add(post)
    db.flush()

    if req.tags:
        sync_post_tags(db, post, req.tags)

    db.commit()
    db.refresh(post)

    return format_api_response(
        success=True,
        message="Post created successfully",
        data=serialize_post(post, include_content=True, db=db),
    )


@router.put("/{id}", response_model=ApiResponse)
def update_post(
    id: int,
    req: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this article.",
        )

    if req.title is not None:
        post.title = req.title.strip()
        if req.slug:
            post.slug = get_unique_slug(db, Post, slugify(req.slug), current_id=id)
        elif not post.slug:
            post.slug = get_unique_slug(db, Post, slugify(req.title), current_id=id)

    if req.slug and req.title is None:
        post.slug = get_unique_slug(db, Post, slugify(req.slug), current_id=id)

    if req.excerpt is not None:
        post.excerpt = req.excerpt.strip() if req.excerpt else None

    if req.content is not None:
        post.content = sanitize_html(req.content)
        post.reading_time_minutes = calculate_reading_time(post.content)

    if req.featured_image is not None:
        post.featured_image = req.featured_image.strip() if req.featured_image else None

    if req.category_id is not None:
        if req.category_id == 0:
            post.category_id = None
        else:
            cat = db.query(Category).filter(Category.id == req.category_id).first()
            if not cat:
                raise HTTPException(status_code=400, detail="Invalid category ID")
            post.category_id = req.category_id

    if req.status is not None:
        if req.status in ["draft", "published", "archived"]:
            if req.status == "published" and not post.published_at:
                post.published_at = datetime.utcnow()
            post.status = req.status

    if req.is_featured is not None:
        post.is_featured = bool(req.is_featured)

    if req.published_at is not None:
        post.published_at = req.published_at

    if req.tags is not None:
        sync_post_tags(db, post, req.tags)

    db.commit()
    db.refresh(post)

    return format_api_response(
        success=True,
        message="Post updated successfully",
        data=serialize_post(post, include_content=True, db=db),
    )


@router.delete("/{id}", response_model=ApiResponse)
def delete_post(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this article.",
        )

    db.delete(post)
    db.commit()

    return format_api_response(
        success=True,
        message="Post deleted successfully",
        data={},
    )


@router.patch("/{id}/publish", response_model=ApiResponse)
def publish_post(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    post.status = "published"
    if not post.published_at:
        post.published_at = datetime.utcnow()
    db.commit()
    db.refresh(post)

    return format_api_response(
        success=True,
        message="Post published successfully",
        data=serialize_post(post, include_content=False, db=db),
    )


@router.patch("/{id}/unpublish", response_model=ApiResponse)
def unpublish_post(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    post.status = "draft"
    db.commit()
    db.refresh(post)

    return format_api_response(
        success=True,
        message="Post unpublished and returned to draft",
        data=serialize_post(post, include_content=False, db=db),
    )


@router.get("/{id}/related", response_model=ApiResponse)
def get_related_posts(
    id: int,
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    tag_ids = [t.id for t in post.tags]

    related_query = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.tags),
        )
        .filter(Post.id != id, Post.status == "published")
    )

    conditions = []
    if post.category_id:
        conditions.append(Post.category_id == post.category_id)
    if tag_ids:
        conditions.append(Post.tags.any(Tag.id.in_(tag_ids)))

    if conditions:
        related_query = related_query.filter(or_(*conditions))

    related = related_query.order_by(desc(Post.published_at)).limit(limit).all()

    if len(related) < limit:
        needed = limit - len(related)
        already_ids = [r.id for r in related] + [id]
        fallback = (
            db.query(Post)
            .options(
                joinedload(Post.author),
                joinedload(Post.category),
                joinedload(Post.tags),
            )
            .filter(Post.id.notin_(already_ids), Post.status == "published")
            .order_by(desc(Post.published_at))
            .limit(needed)
            .all()
        )
        related.extend(fallback)

    items = [serialize_post(p, include_content=False, db=db) for p in related]

    return format_api_response(
        success=True,
        message="Related posts retrieved",
        data=items,
    )
