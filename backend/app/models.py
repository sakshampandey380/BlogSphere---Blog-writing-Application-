from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Enum,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    Index,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.mysql import LONGTEXT
from .database import Base

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(191), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("user", "admin", name="user_role_enum"), nullable=False, default="user", index=True)
    profile_image = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    categories_created = relationship("Category", back_populates="creator")
    comments = relationship("Comment", back_populates="user")
    views = relationship("PostView", back_populates="user")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False)
    theme = Column(Enum("light", "dark", "system", name="theme_enum"), nullable=False, default="light")
    email_notifications = Column(Boolean, nullable=False, default=True)
    comment_notifications = Column(Boolean, nullable=False, default=True)
    post_visibility = Column(Enum("public", "private", name="post_vis_enum"), nullable=False, default="public")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="settings")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    creator = relationship("User", back_populates="categories_created")
    posts = relationship("Post", back_populates="category")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    excerpt = Column(String(1000), nullable=True)
    content = Column(LONGTEXT().with_variant(Text, "sqlite"), nullable=False)
    featured_image = Column(String(1000), nullable=True)
    status = Column(Enum("draft", "published", "archived", name="post_status_enum"), nullable=False, default="draft", index=True)
    is_featured = Column(Boolean, nullable=False, default=False, index=True)
    views_count = Column(BigInteger, nullable=False, default=0)
    reading_time_minutes = Column(Integer, nullable=False, default=1)
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    post_views = relationship("PostView", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_posts_status_date", "status", "published_at"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    posts = relationship("Post", secondary=post_tags, back_populates="tags")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    parent_comment_id = Column(BigInteger, ForeignKey("comments.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True)
    guest_name = Column(String(100), nullable=True)
    guest_email = Column(String(191), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(Enum("pending", "approved", "rejected", "spam", name="comment_status_enum"), nullable=False, default="approved", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")
    replies = relationship("Comment", backref=backref("parent", remote_side=[id]), cascade="all, delete-orphan")


class PostView(Base):
    __tablename__ = "post_views"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True, index=True)
    visitor_identifier = Column(String(191), nullable=True, index=True)
    ip_hash = Column(String(255), nullable=True)
    user_agent = Column(String(500), nullable=True)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    post = relationship("Post", back_populates="post_views")
    user = relationship("User", back_populates="views")
