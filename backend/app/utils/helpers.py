import re
import math
from typing import Any, Optional
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session


def slugify(text: str) -> str:
    if not text:
        return "untitled-post"
    slug = text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug or "post"


def get_unique_slug(db: Session, model: Any, base_slug: str, current_id: Optional[int] = None) -> str:
    slug = base_slug
    counter = 1

    while True:
        query = db.query(model).filter(model.slug == slug)
        if current_id is not None:
            query = query.filter(model.id != current_id)
        existing = query.first()

        if not existing:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def calculate_reading_time(content: str, words_per_minute: int = 200) -> int:
    if not content:
        return 1
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    if word_count == 0:
        return 1
    minutes = math.ceil(word_count / words_per_minute)
    return max(1, minutes)


def format_api_response(success: bool, message: str, data: Any = None, errors: Any = None) -> dict:
    resp = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
    }
    if errors is not None:
        resp["errors"] = errors
    return resp
