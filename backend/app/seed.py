from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.database import SessionLocal, engine, Base
from backend.app.models import User, UserSettings, Category, Tag, Post, Comment, PostView
from backend.app.utils.security import hash_password
from backend.app.utils.helpers import calculate_reading_time, slugify

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("[SEED] Starting database seed process...")

        users_data = [
            {
                "email": "admin@blogsphere.dev",
                "name": "Saksham Pandey",
                "password": "AdminPassword123!",
                "role": "admin",
                "bio": "Lead software architect and creator of BlogSphere. Focused on high-scale distributed systems, Python, and modern web architectures.",
                "profile_image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80"
            },
            {
                "email": "alex.morgan@blogsphere.dev",
                "name": "Alex Morgan",
                "password": "AuthorPassword123!",
                "role": "user",
                "bio": "Full-stack engineer, open-source enthusiast, and backend developer passionate about clean API design.",
                "profile_image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80"
            },
            {
                "email": "sophia.chen@blogsphere.dev",
                "name": "Sophia Chen",
                "password": "AuthorPassword123!",
                "role": "user",
                "bio": "Cybersecurity researcher and cloud infrastructure engineer exploring zero-trust environments and defensive architectures.",
                "profile_image": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=300&q=80"
            }
        ]

        user_map = {}
        for u in users_data:
            user = db.query(User).filter(User.email == u["email"]).first()
            if not user:
                user = User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    bio=u["bio"],
                    profile_image=u["profile_image"],
                    is_active=True,
                    last_login=datetime.utcnow()
                )
                db.add(user)
                db.flush()

                settings = UserSettings(
                    user_id=user.id,
                    theme="light",
                    email_notifications=True,
                    comment_notifications=True,
                    post_visibility="public"
                )
                db.add(settings)
                print(f"  + Created User: {u['name']} ({u['email']}) [Role: {u['role']}]")
            user_map[u["email"]] = user

        db.commit()

        categories_data = [
            ("Technology", "technology", "Technology, software and emerging innovations."),
            ("Artificial Intelligence", "artificial-intelligence", "AI, machine learning and generative artificial intelligence."),
            ("Programming", "programming", "Programming languages, architectural concepts and software development."),
            ("Web Development", "web-development", "Frontend, backend, modern web APIs, and full-stack development."),
            ("Cybersecurity", "cybersecurity", "Cybersecurity defense, security practices, privacy and online safety."),
            ("Tutorials", "tutorials", "Step-by-step technical guides, tutorials and practical walkthroughs."),
            ("Productivity", "productivity", "Developer workflows, tooling, efficiency and productive habits."),
            ("Business", "business", "Tech startups, digital enterprise and software business models."),
        ]

        cat_map = {}
        for name, slug, desc in categories_data:
            cat = db.query(Category).filter(Category.slug == slug).first()
            if not cat:
                cat = Category(name=name, slug=slug, description=desc, created_by=user_map["admin@blogsphere.dev"].id)
                db.add(cat)
                db.flush()
                print(f"  + Created Category: {name}")
            cat_map[slug] = cat

        db.commit()

        tags_data = [
            ("AI", "ai"),
            ("Python", "python"),
            ("FastAPI", "fastapi"),
            ("JavaScript", "javascript"),
            ("HTML", "html"),
            ("CSS", "css"),
            ("React", "react"),
            ("MySQL", "mysql"),
            ("Web Development", "web-development"),
            ("Cybersecurity", "cybersecurity"),
            ("Programming", "programming"),
            ("Tutorial", "tutorial"),
            ("Technology", "technology")
        ]

        tag_map = {}
        for name, slug in tags_data:
            tag = db.query(Tag).filter(Tag.slug == slug).first()
            if not tag:
                tag = Tag(name=name, slug=slug)
                db.add(tag)
                db.flush()
                print(f"  + Created Tag: {name}")
            tag_map[slug] = tag

        db.commit()

        posts_data = [
            {
                "title": "How AI Is Changing Modern Web Development",
                "slug": "how-ai-is-changing-modern-web-development",
                "author": "admin@blogsphere.dev",
                "category": "artificial-intelligence",
                "excerpt": "Discover how artificial intelligence and LLM-driven tooling are transforming the way engineers architect, build, and deploy production software.",
                "featured_image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True,
                "status": "published",
                "views_count": 1420,
                "published_days_ago": 2,
                "tags": ["ai", "web-development", "technology"],
                "content": """
<h2>The New Paradigm of Intelligent Development</h2>
<p>Over the past decade, web engineering has undergone continuous structural transformation—from server-rendered monolithic templates to client-heavy single page applications, micro-frontends, and serverless edge functions. Today, an even more profound shift is underway: the deep integration of <strong>generative artificial intelligence</strong> into every stage of the software delivery lifecycle.</p>

<p>Rather than merely automating boilerplate syntax, modern AI systems have evolved into collaborative peer architects. They assist developers in planning schema definitions, reasoning through subtle edge cases in asynchronous state machines, and generating resilient unit tests.</p>

<h3>1. Automated API Contract Generation & Type Inference</h3>
<p>One of the most immediate productivity breakthroughs is occurring at the boundary between client and server. Modern teams frequently spend hundreds of hours maintaining OpenAPI schemas, TypeScript interfaces, and validation rules in parallel.</p>

<pre><code class="language-python"># Declarative FastAPI endpoint with typed contract
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field

class ArticlePayload(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    category: str
    tags: list[str] = []

@app.post("/api/v1/articles")
async def publish_article(payload: ArticlePayload):
    # AI-assisted validation and semantic tagging
    return {"status": "published", "title": payload.title}
</code></pre>

<blockquote>"AI tools do not replace critical thinking; they amplify clarity and compress the feedback loop between conceptual design and executable code."</blockquote>

<h3>2. Intelligent Observability and Real-time Auditing</h3>
<p>Modern applications generate mountains of logs, traces, and metrics. Automated telemetry tools now digest runtime diagnostics, identify anomalous CPU spikes or slow database queries before users notice them, and suggest actionable indexes.</p>

<h3>Looking Ahead</h3>
<p>As we design future web experiences, developers who embrace intelligent workflow automation while maintaining strict foundational engineering discipline will build faster, more reliable, and delightfully accessible web platforms.</p>
"""
            },
            {
                "title": "Getting Started With FastAPI: Building High-Performance Python APIs",
                "slug": "getting-started-with-fastapi-building-high-performance-python-apis",
                "author": "alex.morgan@blogsphere.dev",
                "category": "programming",
                "excerpt": "A hands-on guide to constructing blazing fast, production-ready REST APIs using FastAPI, Pydantic v2, and asynchronous Python.",
                "featured_image": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",
                "is_featured": True,
                "status": "published",
                "views_count": 985,
                "published_days_ago": 5,
                "tags": ["python", "fastapi", "programming", "tutorial"],
                "content": """
<h2>Why FastAPI Dominates the Modern Python Ecosystem</h2>
<p>For years, Python developers had to choose between the monolithic richness of Django and the minimalist flexibility of Flask. While both remain exceptional frameworks, the arrival of <strong>FastAPI</strong> changed expectations by combining raw performance with automatic documentation and strict type checking.</p>

<p>Under the hood, FastAPI is powered by <strong>Starlette</strong> for high-throughput asynchronous networking and <strong>Pydantic</strong> for data parsing and validation.</p>

<h3>Key Architectural Benefits</h3>
<ul>
    <li><strong>Automatic Interactive Docs:</strong> Every route instantly generates Swagger UI at <code>/docs</code> and ReDoc at <code>/redoc</code>.</li>
    <li><strong>Type Safety:</strong> Python standard type hints eliminate thousands of runtime typing bugs.</li>
    <li><strong>Asynchronous Core:</strong> Native <code>async</code> and <code>await</code> support enables thousands of concurrent I/O connections.</li>
</ul>

<h3>Writing Clean Dependency Injection</h3>
<p>FastAPI's dependency injection system allows database sessions, authentication checks, and rate-limiting rules to be composed with minimal coupling:</p>

<pre><code class="language-python">from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = authenticate_token(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user
</code></pre>

<p>This design makes testing straightforward since dependencies can be overridden during automated test runs without altering application source code.</p>
"""
            },
            {
                "title": "Defensive Architecture: Essential Cybersecurity Practices for 2026",
                "slug": "defensive-architecture-essential-cybersecurity-practices-for-2026",
                "author": "sophia.chen@blogsphere.dev",
                "category": "cybersecurity",
                "excerpt": "Learn how to protect modern web applications from SQL injection, cross-site scripting (XSS), credential stuffing, and session hijacking.",
                "featured_image": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "status": "published",
                "views_count": 750,
                "published_days_ago": 7,
                "tags": ["cybersecurity", "technology", "programming"],
                "content": """
<h2>Security Is Not a Feature; It Is an Invariant</h2>
<p>Too often, cybersecurity is treated as an afterthought—a checklist addressed right before an application goes to production. In modern internet environments, automated scanners and bots probe public endpoints within seconds of DNS propagation.</p>

<h3>1. Parameterized Queries and ORM Defense</h3>
<p>SQL Injection remains one of the oldest vulnerabilities, yet it continues to appear in audits. Parameterized queries and modern ORMs such as SQLAlchemy ensure user inputs are treated strictly as data literals rather than executable SQL syntax.</p>

<h3>2. Content Sanitization and XSS Prevention</h3>
<p>When allowing users to post rich text, never render unsanitized HTML directly into the DOM. Malicious inputs can embed script tags or disguise payloads inside event attributes like <code>onload</code> or <code>onerror</code>.</p>

<blockquote>"Always validate on the backend. Frontend validation is for user experience; backend validation is for security."</blockquote>

<h3>3. Modern Token Hygiene</h3>
<p>Ensure JSON Web Tokens (JWT) are signed with robust cryptographic algorithms (e.g., HS256 with high-entropy secrets or RS256/Ed25519) and enforce reasonable expiration windows to mitigate the risk of token exfiltration.</p>
"""
            },
            {
                "title": "Modern JavaScript Architecture: Clean State and Component Design",
                "slug": "modern-javascript-architecture-clean-state-and-component-design",
                "author": "admin@blogsphere.dev",
                "category": "web-development",
                "excerpt": "Explore vanilla JavaScript patterns, modular architecture, and modern browser APIs that yield fast, zero-bloat web applications.",
                "featured_image": "https://images.unsplash.com/photo-1579468118864-ddb89ea93339?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "status": "published",
                "views_count": 890,
                "published_days_ago": 10,
                "tags": ["javascript", "web-development", "html", "css"],
                "content": """
<h2>Revisiting Vanilla JavaScript in the Modern Era</h2>
<p>Modern web standards have evolved dramatically. Native custom elements, CSS custom properties, fetch API, and lightweight reactive primitives mean developers can build responsive, highly capable web applications without downloading megabytes of third-party libraries.</p>

<h3>Predictable State Containers</h3>
<p>Using clean pub/sub patterns or localized event buses, modules can coordinate state changes cleanly:</p>

<pre><code class="language-javascript">class Store {
  constructor(initialState = {}) {
    this.state = initialState;
    this.listeners = new Set();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  setState(updates) {
    this.state = { ...this.state, ...updates };
    this.listeners.forEach(fn => fn(this.state));
  }
}
</code></pre>

<p>By pairing focused, lightweight patterns with semantic HTML5 markup, web applications render in milliseconds and run silky smooth across both mobile and desktop devices.</p>
"""
            },
            {
                "title": "Mastering Database Indexing and Performance in MySQL",
                "slug": "mastering-database-indexing-and-performance-in-mysql",
                "author": "alex.morgan@blogsphere.dev",
                "category": "tutorials",
                "excerpt": "Demystifying B-Tree indexes, composite keys, query execution plans, and normalization strategies in MySQL and InnoDB.",
                "featured_image": "https://images.unsplash.com/photo-1544383835-bda2bc66a55d?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "status": "published",
                "views_count": 620,
                "published_days_ago": 14,
                "tags": ["mysql", "tutorial", "programming"],
                "content": """
<h2>The Hidden Cost of Full Table Scans</h2>
<p>When an application begins with a few dozen rows in development, every query responds in under a millisecond. However, as tables scale into hundreds of thousands of records, unindexed filtering causes the database engine to perform expensive disk reads across entire tables.</p>

<h3>Understanding Composite Indexes</h3>
<p>In our BlogSphere platform, we frequently query published articles ordered by their publication date:</p>

<pre><code class="language-sql">SELECT * FROM posts 
WHERE status = 'published' 
ORDER BY published_at DESC;
</code></pre>

<p>A composite index on <code>(status, published_at)</code> allows InnoDB to satisfy both the <code>WHERE</code> filtering condition and the <code>ORDER BY</code> sorting order in a single index lookup, eliminating expensive temporary filesort operations.</p>
"""
            },
            {
                "title": "Designing Intuitive User Interfaces: Spacing, Contrast, and Hierarchy",
                "slug": "designing-intuitive-user-interfaces-spacing-contrast-and-hierarchy",
                "author": "sophia.chen@blogsphere.dev",
                "category": "productivity",
                "excerpt": "A comprehensive primer on crafting accessible, professional interfaces using intentional typography, clear visual hierarchy, and cohesive design tokens.",
                "featured_image": "https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "status": "published",
                "views_count": 510,
                "published_days_ago": 18,
                "tags": ["css", "html", "web-development"],
                "content": """
<h2>The Foundation of Great Design</h2>
<p>Great design does not originate from flashy decorations or overwhelming gradients. It stems from thoughtful spacing, clear contrast ratios, legible typography, and intuitive interaction patterns.</p>

<h3>The 8pt Grid System</h3>
<p>By constraining spacing increments (margins, padding, gap) to multiples of 4px and 8px (4, 8, 12, 16, 24, 32, 48, 64), interfaces achieve natural optical harmony and effortless alignment across responsive screen sizes.</p>

<h3>Dark Mode That Doesn't Strain the Eyes</h3>
<p>True black (<code>#000000</code>) against pure white creates harsh optical vibrations. Instead, use soft off-blacks (such as <code>#0f172a</code> or <code>#111827</code>) with warm neutral grays to provide comfortable reading over prolonged sessions.</p>
"""
            },
            {
                "title": "Building Scalable Microservices with Asynchronous Messaging (Draft)",
                "slug": "building-scalable-microservices-with-asynchronous-messaging",
                "author": "admin@blogsphere.dev",
                "category": "programming",
                "excerpt": "A work-in-progress exploration of event-driven architectures, dead letter queues, and consumer group scaling.",
                "featured_image": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&q=80",
                "is_featured": False,
                "status": "draft",
                "views_count": 0,
                "published_days_ago": None,
                "tags": ["programming", "technology"],
                "content": """
<p>This article is currently an unpublished draft reserved for author review.</p>
<p>We are detailing asynchronous queue patterns and fault tolerance strategies for large-scale distributed architectures.</p>
"""
            }
        ]

        for p in posts_data:
            existing_post = db.query(Post).filter(Post.slug == p["slug"]).first()
            if not existing_post:
                author_user = user_map[p["author"]]
                cat_obj = cat_map.get(p["category"])
                pub_date = (
                    datetime.utcnow() - timedelta(days=p["published_days_ago"])
                    if p["published_days_ago"] is not None
                    else None
                )

                post = Post(
                    author_id=author_user.id,
                    category_id=cat_obj.id if cat_obj else None,
                    title=p["title"],
                    slug=p["slug"],
                    excerpt=p["excerpt"],
                    content=p["content"].strip(),
                    featured_image=p["featured_image"],
                    status=p["status"],
                    is_featured=p["is_featured"],
                    views_count=p["views_count"],
                    reading_time_minutes=calculate_reading_time(p["content"]),
                    published_at=pub_date,
                    created_at=pub_date if pub_date else datetime.utcnow()
                )
                db.add(post)
                db.flush()

                post_tags_list = [tag_map[t_slug] for t_slug in p["tags"] if t_slug in tag_map]
                post.tags = post_tags_list

                print(f"  + Created Post: '{p['title']}' [{p['status'].upper()}]")

                if p["status"] == "published":
                    c1 = Comment(
                        post_id=post.id,
                        user_id=user_map["alex.morgan@blogsphere.dev"].id,
                        content="Fantastic breakdown! The code example with FastAPI's Pydantic validation is concise and practical.",
                        status="approved",
                        created_at=datetime.utcnow() - timedelta(days=1)
                    )
                    db.add(c1)
                    db.flush()

                    c2 = Comment(
                        post_id=post.id,
                        user_id=None,
                        guest_name="David Miller",
                        guest_email="david@example.com",
                        content="Really appreciate the insights on indexing and defensive coding. Looking forward to more articles on BlogSphere!",
                        status="approved",
                        created_at=datetime.utcnow() - timedelta(hours=8)
                    )
                    db.add(c2)

        db.commit()
        print("[SEED] Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Failed to seed database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
