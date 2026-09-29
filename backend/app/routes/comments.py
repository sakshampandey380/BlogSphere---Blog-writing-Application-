from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from ..database import get_db
from ..models import Comment, Post, User
from ..schemas import CommentCreate, ApiResponse
from ..auth import get_optional_user, get_current_user
from ..utils.sanitizer import sanitize_html
from ..utils.helpers import format_api_response

router = APIRouter(prefix="/api/posts", tags=["Comments"])


def serialize_comment(c: Comment) -> dict:
    return {
        "id": c.id,
        "post_id": c.post_id,
        "user_id": c.user_id,
        "guest_name": c.guest_name,
        "parent_comment_id": c.parent_comment_id,
        "content": c.content,
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "user": {
            "id": c.user.id,
            "name": c.user.name,
            "profile_image": c.user.profile_image,
            "role": c.user.role,
        } if c.user else None,
        "replies": [serialize_comment(r) for r in c.replies if r.status == "approved"] if hasattr(c, "replies") and c.replies else []
    }


@router.get("/{post_id}/comments", response_model=ApiResponse)
def get_post_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    top_level_comments = (
        db.query(Comment)
        .options(
            joinedload(Comment.user),
            joinedload(Comment.replies).joinedload(Comment.user)
        )
        .filter(
            Comment.post_id == post_id,
            Comment.parent_comment_id == None,
            Comment.status == "approved"
        )
        .order_by(desc(Comment.created_at))
        .all()
    )

    data = [serialize_comment(c) for c in top_level_comments]

    return format_api_response(
        success=True,
        message="Comments retrieved",
        data=data
    )


@router.post("/{post_id}/comments", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    req: CommentCreate,
    current_user: User = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Article not found")

    if post.status != "published":
        raise HTTPException(status_code=400, detail="Cannot comment on unpublished articles.")

    clean_text = sanitize_html(req.content).strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Comment content cannot be empty.")

    if req.parent_comment_id:
        parent = db.query(Comment).filter(Comment.id == req.parent_comment_id, Comment.post_id == post_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent comment not found")

    if current_user:
        user_id = current_user.id
        guest_name = current_user.name
        guest_email = current_user.email
    else:
        user_id = None
        guest_name = req.guest_name.strip() if req.guest_name else "Guest Reader"
        guest_email = req.guest_email

    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        parent_comment_id=req.parent_comment_id,
        guest_name=guest_name,
        guest_email=guest_email,
        content=clean_text,
        status="approved"
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return format_api_response(
        success=True,
        message="Comment submitted successfully",
        data=serialize_comment(comment)
    )


comments_admin_router = APIRouter(prefix="/api/comments", tags=["Comments"])


@comments_admin_router.delete("/{comment_id}", response_model=ApiResponse)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).options(joinedload(Comment.post)).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    is_comment_author = comment.user_id == current_user.id
    is_post_author = comment.post.author_id == current_user.id
    is_admin = current_user.role == "admin"

    if not (is_comment_author or is_post_author or is_admin):
        raise HTTPException(status_code=403, detail="You do not have permission to delete this comment.")

    db.delete(comment)
    db.commit()

    return format_api_response(
        success=True,
        message="Comment deleted successfully",
        data={}
    )
