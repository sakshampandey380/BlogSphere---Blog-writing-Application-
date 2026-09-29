from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
from ..database import get_db
from ..models import Post, User, Comment, Category
from ..schemas import ApiResponse
from ..auth import get_current_user
from ..utils.helpers import format_api_response
from .posts import serialize_post

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=ApiResponse)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve statistical counters for the authenticated user's dashboard."""
    user_id = current_user.id
    is_admin = current_user.role == "admin"

    # User-specific post statistics
    total_posts = db.query(Post).filter(Post.author_id == user_id).count()
    published_posts = db.query(Post).filter(Post.author_id == user_id, Post.status == "published").count()
    draft_posts = db.query(Post).filter(Post.author_id == user_id, Post.status == "draft").count()
    featured_posts = db.query(Post).filter(Post.author_id == user_id, Post.is_featured == 1).count()

    # Total views across author's posts
    views_sum = (
        db.query(func.coalesce(func.sum(Post.views_count), 0))
        .filter(Post.author_id == user_id)
        .scalar()
    )

    # Total comments received across author's posts
    comments_count = (
        db.query(Comment)
        .join(Post, Post.id == Comment.post_id)
        .filter(Post.author_id == user_id)
        .count()
    )

    stats = {
        "user_stats": {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "draft_posts": draft_posts,
            "featured_posts": featured_posts,
            "total_views": int(views_sum),
            "total_comments": comments_count,
        }
    }

    # If admin, append platform-wide statistics
    if is_admin:
        site_total_posts = db.query(Post).count()
        site_published = db.query(Post).filter(Post.status == "published").count()
        site_drafts = db.query(Post).filter(Post.status == "draft").count()
        site_users = db.query(User).count()
        site_views = db.query(func.coalesce(func.sum(Post.views_count), 0)).scalar()
        site_categories = db.query(Category).count()

        stats["admin_stats"] = {
            "site_total_posts": site_total_posts,
            "site_published_posts": site_published,
            "site_draft_posts": site_drafts,
            "site_users_count": site_users,
            "site_views_count": int(site_views),
            "site_categories_count": site_categories,
        }

    return format_api_response(
        success=True,
        message="Dashboard statistics retrieved",
        data=stats
    )


@router.get("/posts", response_model=ApiResponse)
def get_dashboard_posts(
    scope: str = Query("mine", pattern="^(mine|all)$"),
    status: str = Query("all"),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve posts for dashboard management."""
    query = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.category),
            joinedload(Post.tags),
        )
    )

    # Scope filtering: only admins can view all
    if scope == "all" and current_user.role == "admin":
        pass  # Query all posts across system
    else:
        query = query.filter(Post.author_id == current_user.id)

    # Status filter
    if status and status != "all":
        query = query.filter(Post.status == status)

    # Search filter
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Post.title.ilike(s),
                Post.excerpt.ilike(s),
            )
        )

    posts = query.order_by(desc(Post.created_at)).all()

    items = [serialize_post(p, include_content=False, db=db) for p in posts]

    return format_api_response(
        success=True,
        message="Dashboard posts retrieved",
        data=items
    )
