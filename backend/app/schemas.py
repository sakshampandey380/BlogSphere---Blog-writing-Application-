from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    role: Optional[str] = "user"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = None
    profile_image: Optional[str] = None


class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = "light"
    email_notifications: Optional[bool] = True
    comment_notifications: Optional[bool] = True
    post_visibility: Optional[str] = "public"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    created_at: datetime
    posts_count: Optional[int] = 0


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theme: str
    email_notifications: bool
    comment_notifications: bool
    post_visibility: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    posts_count: Optional[int] = 0


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: Optional[str] = None


class TagCreate(TagBase):
    pass


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class PostBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    slug: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: str = Field(..., min_length=10)
    featured_image: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = "draft"
    is_featured: Optional[bool] = False
    published_at: Optional[datetime] = None
    tags: Optional[List[str]] = []


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    slug: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, min_length=10)
    featured_image: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None
    published_at: Optional[datetime] = None
    tags: Optional[List[str]] = None


class PostListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    status: str
    is_featured: bool
    views_count: int
    reading_time_minutes: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    category: Optional[CategoryResponse] = None
    tags: List[TagResponse] = []


class PostDetailResponse(PostListItemResponse):
    content: str
    comments_count: Optional[int] = 0


class PaginatedPostsResponse(BaseModel):
    items: List[PostListItemResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=2, max_length=2000)
    guest_name: Optional[str] = None
    guest_email: Optional[EmailStr] = None
    parent_comment_id: Optional[int] = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: Optional[int] = None
    guest_name: Optional[str] = None
    content: str
    status: str
    created_at: datetime
    user: Optional[UserResponse] = None
    replies: Optional[List["CommentResponse"]] = []


class DashboardStatsResponse(BaseModel):
    total_posts: int
    published_posts: int
    draft_posts: int
    featured_posts: int
    total_views: int
    total_comments: int


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[Any] = None
