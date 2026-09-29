/**
 * BlogSphere - Public Posts & Article Details Engine
 */

let currentPage = 1;
let currentCategory = "";
let currentTag = "";
let currentSearch = "";
let searchTimeout = null;

// Determine relative path prefix depending on if in /pages or root
function getAssetPath(filename) {
  const isRoot = window.location.pathname.endsWith("index.html") || window.location.pathname === "/" || window.location.pathname.endsWith("QSkills - Task -2/") || window.location.pathname.endsWith("frontend/");
  const prefix = isRoot ? (window.location.port === "8000" ? "/assets" : "./assets") : "../assets";
  return `${prefix}/${filename}`;
}

function getPagePath(pageName) {
  const isRoot = window.location.pathname.endsWith("index.html") || window.location.pathname === "/" || window.location.pathname.endsWith("QSkills - Task -2/") || window.location.pathname.endsWith("frontend/");
  const prefix = isRoot ? (window.location.port === "8000" ? "/pages" : "./pages") : ".";
  return `${prefix}/${pageName}`;
}

// ---------------------------------------------------------
// 1. HOMEPAGE: Initialize Categories & Posts Feed
// ---------------------------------------------------------
export async function initHomePage() {
  // Check URL query parameters for initial search, category or tag
  const urlParams = new URLSearchParams(window.location.search);
  currentCategory = urlParams.get("category") || "";
  currentTag = urlParams.get("tag") || "";
  currentSearch = urlParams.get("search") || "";

  const searchInput = document.getElementById("search-input");
  const clearSearchBtn = document.getElementById("search-clear-btn");
  if (searchInput && currentSearch) {
    searchInput.value = currentSearch;
    if (clearSearchBtn) clearSearchBtn.style.display = "block";
  }

  // Load categories and posts in parallel
  await Promise.all([loadCategories(), loadPostsFeed()]);

  // Setup Search Input event
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const val = e.target.value.trim();
      if (clearSearchBtn) clearSearchBtn.style.display = val ? "block" : "none";

      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        currentSearch = val;
        currentPage = 1;
        updateUrlParams();
        loadPostsFeed();
      }, 350);
    });

    if (clearSearchBtn) {
      clearSearchBtn.addEventListener("click", () => {
        searchInput.value = "";
        clearSearchBtn.style.display = "none";
        currentSearch = "";
        currentPage = 1;
        updateUrlParams();
        loadPostsFeed();
      });
    }
  }
}

function updateUrlParams() {
  const params = new URLSearchParams();
  if (currentCategory) params.set("category", currentCategory);
  if (currentTag) params.set("tag", currentTag);
  if (currentSearch) params.set("search", currentSearch);
  const newUrl = `${window.location.pathname}${params.toString() ? "?" + params.toString() : ""}`;
  window.history.replaceState({}, "", newUrl);
}

// ---------------------------------------------------------
// 2. Load Categories Bar
// ---------------------------------------------------------
async function loadCategories() {
  const container = document.getElementById("category-pills");
  if (!container) return;

  try {
    const res = await window.api.get("/categories");
    if (res && res.success && res.data) {
      const categories = res.data;
      let html = `
        <button class="category-pill ${!currentCategory && !currentTag ? "active" : ""}" data-slug="">
          All Posts
        </button>
      `;

      categories.forEach((cat) => {
        const isActive = currentCategory === cat.slug;
        html += `
          <button class="category-pill ${isActive ? "active" : ""}" data-slug="${cat.slug}">
            ${cat.name}
            <span class="pill-count">${cat.posts_count || 0}</span>
          </button>
        `;
      });

      container.innerHTML = html;

      // Attach Click Handlers
      container.querySelectorAll(".category-pill").forEach((pill) => {
        pill.addEventListener("click", () => {
          container.querySelectorAll(".category-pill").forEach((p) => p.classList.remove("active"));
          pill.classList.add("active");
          currentCategory = pill.getAttribute("data-slug");
          currentTag = ""; // clear tag filter when selecting a category
          currentPage = 1;
          updateUrlParams();
          loadPostsFeed();
        });
      });
    }
  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

// ---------------------------------------------------------
// 3. Load Posts Feed & Featured Post
// ---------------------------------------------------------
async function loadPostsFeed() {
  const gridContainer = document.getElementById("posts-grid");
  const featuredContainer = document.getElementById("featured-post-container");
  const paginationContainer = document.getElementById("pagination-container");

  if (gridContainer) {
    gridContainer.innerHTML = window.renderCardSkeleton(6);
  }

  try {
    const params = {
      page: currentPage,
      limit: 9,
      category: currentCategory,
      tag: currentTag,
      search: currentSearch,
      status: "published",
    };

    const res = await window.api.get("/posts", params);
    if (!res || !res.success || !res.data) {
      throw new Error("Unable to fetch articles.");
    }

    const { items, total, total_pages } = res.data;

    // Active filter banner if searching or tagged
    renderActiveFilterNotice();

    // 1. Featured Post (Only show on page 1 with no search filter)
    if (featuredContainer) {
      if (currentPage === 1 && !currentSearch && !currentCategory && !currentTag) {
        const featuredItem = items.find((p) => p.is_featured) || items[0];
        if (featuredItem) {
          featuredContainer.innerHTML = renderFeaturedPostCard(featuredItem);
          featuredContainer.style.display = "block";
        } else {
          featuredContainer.style.display = "none";
        }
      } else {
        featuredContainer.style.display = "none";
      }
    }

    // 2. Posts Grid
    if (items.length === 0) {
      gridContainer.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">🔍</div>
          <h3 class="empty-state-title">No articles found</h3>
          <p class="empty-state-desc">
            ${currentSearch ? `No matches for "${currentSearch}".` : "There are no published articles in this section yet."}
          </p>
          <button class="btn btn-outline btn-sm" id="btn-reset-filters">Clear Filters</button>
        </div>
      `;
      const resetBtn = document.getElementById("btn-reset-filters");
      if (resetBtn) {
        resetBtn.addEventListener("click", () => {
          currentCategory = "";
          currentTag = "";
          currentSearch = "";
          const input = document.getElementById("search-input");
          if (input) input.value = "";
          const clearBtn = document.getElementById("search-clear-btn");
          if (clearBtn) clearBtn.style.display = "none";
          currentPage = 1;
          updateUrlParams();
          loadCategories();
          loadPostsFeed();
        });
      }
    } else {
      gridContainer.innerHTML = items.map((p) => renderPostCard(p)).join("");
    }

    // 3. Pagination Controls
    if (paginationContainer) {
      if (total_pages > 1) {
        paginationContainer.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: center; gap: 0.75rem; margin-top: 2rem;">
            <button class="btn btn-secondary btn-sm" id="prev-page-btn" ${currentPage === 1 ? "disabled" : ""}>
              ← Previous
            </button>
            <span style="font-size: 0.9rem; font-weight: 600; color: var(--text-muted);">
              Page ${currentPage} of ${total_pages}
            </span>
            <button class="btn btn-secondary btn-sm" id="next-page-btn" ${currentPage === total_pages ? "disabled" : ""}>
              Next →
            </button>
          </div>
        `;

        const prevBtn = document.getElementById("prev-page-btn");
        const nextBtn = document.getElementById("next-page-btn");

        if (prevBtn) {
          prevBtn.onclick = () => {
            if (currentPage > 1) {
              currentPage--;
              loadPostsFeed();
              window.scrollTo({ top: 400, behavior: "smooth" });
            }
          };
        }
        if (nextBtn) {
          nextBtn.onclick = () => {
            if (currentPage < total_pages) {
              currentPage++;
              loadPostsFeed();
              window.scrollTo({ top: 400, behavior: "smooth" });
            }
          };
        }
      } else {
        paginationContainer.innerHTML = "";
      }
    }
  } catch (err) {
    if (gridContainer) {
      gridContainer.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">⚠️</div>
          <h3 class="empty-state-title">Unable to load posts</h3>
          <p class="empty-state-desc">${err.message || "Please make sure your MySQL database and FastAPI server are running."}</p>
          <button class="btn btn-primary btn-sm" onclick="location.reload()">Retry Connection</button>
        </div>
      `;
    }
  }
}

function renderActiveFilterNotice() {
  const noticeContainer = document.getElementById("active-filter-notice");
  if (!noticeContainer) return;

  if (currentSearch || currentTag || currentCategory) {
    let label = "";
    if (currentSearch) label += `Search: "<strong>${currentSearch}</strong>" `;
    if (currentTag) label += `Tag: #<strong>${currentTag}</strong> `;
    if (currentCategory) label += `Category: <strong>${currentCategory}</strong>`;

    noticeContainer.innerHTML = `
      <div style="background: var(--bg-tertiary); border: 1px solid var(--border-default); border-radius: var(--radius-md); padding: 0.6rem 1rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 0.92rem; color: var(--text-secondary);">Showing results for ${label}</span>
        <button class="btn btn-sm btn-outline" id="btn-clear-active-filter" style="padding: 0.25rem 0.6rem; font-size: 0.78rem;">Clear</button>
      </div>
    `;

    document.getElementById("btn-clear-active-filter").onclick = () => {
      currentSearch = "";
      currentTag = "";
      currentCategory = "";
      const searchInput = document.getElementById("search-input");
      if (searchInput) searchInput.value = "";
      const clearBtn = document.getElementById("search-clear-btn");
      if (clearBtn) clearBtn.style.display = "none";
      currentPage = 1;
      updateUrlParams();
      loadCategories();
      loadPostsFeed();
    };
    noticeContainer.style.display = "block";
  } else {
    noticeContainer.style.display = "none";
  }
}

function renderFeaturedPostCard(post) {
  const postUrl = `${getPagePath("post.html")}?slug=${encodeURIComponent(post.slug)}`;
  const defaultThumb = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80";
  const authorAvatar = (post.author && post.author.profile_image) || getAssetPath("default-avatar.svg");

  return `
    <article class="featured-card">
      <div class="featured-image-wrapper">
        <a href="${postUrl}">
          <img src="${post.featured_image || defaultThumb}" alt="${post.title}" class="featured-image" loading="lazy" onerror="this.src='${defaultThumb}'" />
        </a>
      </div>
      <div class="featured-body">
        <div class="featured-badge-row">
          <span class="category-badge">${post.category ? post.category.name : "Article"}</span>
          <span class="reading-time-badge">⏱️ ${post.reading_time_minutes || 1} min read</span>
        </div>
        <h2 class="featured-title">
          <a href="${postUrl}">${post.title}</a>
        </h2>
        <p class="featured-excerpt">${post.excerpt || ""}</p>
        <div class="post-meta-row">
          <div class="author-chip">
            <img src="${authorAvatar}" alt="${post.author ? post.author.name : "Author"}" class="author-chip-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(post.author ? post.author.name : "A")}&background=4f46e5&color=fff'" />
            <div>
              <div class="author-chip-name">${post.author ? post.author.name : "Author"}</div>
              <div class="author-chip-date">${window.formatDate(post.published_at || post.created_at)}</div>
            </div>
          </div>
          <a href="${postUrl}" class="btn btn-primary btn-sm">Read Article →</a>
        </div>
      </div>
    </article>
  `;
}

function renderPostCard(post) {
  const postUrl = `${getPagePath("post.html")}?slug=${encodeURIComponent(post.slug)}`;
  const defaultThumb = "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80";
  const authorAvatar = (post.author && post.author.profile_image) || getAssetPath("default-avatar.svg");

  const tagsHtml = (post.tags || [])
    .slice(0, 3)
    .map((t) => `<a href="?tag=${encodeURIComponent(t.slug)}" class="tag-badge">#${t.name}</a>`)
    .join("");

  return `
    <article class="post-card">
      <div class="post-card-thumb-wrapper">
        <a href="${postUrl}">
          <img src="${post.featured_image || defaultThumb}" alt="${post.title}" class="post-card-thumb" loading="lazy" onerror="this.src='${defaultThumb}'" />
        </a>
      </div>
      <div class="post-card-body">
        <div class="post-card-header">
          <span class="category-badge">${post.category ? post.category.name : "General"}</span>
          <span class="reading-time-badge">${post.reading_time_minutes || 1}m</span>
        </div>
        <h3 class="post-card-title">
          <a href="${postUrl}">${post.title}</a>
        </h3>
        <p class="post-card-excerpt">${post.excerpt || ""}</p>
        <div class="tag-list">${tagsHtml}</div>
        <div class="post-card-footer">
          <div class="author-chip">
            <img src="${authorAvatar}" alt="${post.author ? post.author.name : "Author"}" class="author-chip-avatar" style="width: 28px; height: 28px;" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(post.author ? post.author.name : "A")}&background=4f46e5&color=fff'" />
            <div>
              <div class="author-chip-name" style="font-size: 0.82rem;">${post.author ? post.author.name : "Author"}</div>
              <div class="author-chip-date" style="font-size: 0.72rem;">${window.formatDate(post.published_at || post.created_at)}</div>
            </div>
          </div>
          <a href="${postUrl}" class="read-more-link">Read →</a>
        </div>
      </div>
    </article>
  `;
}

// ---------------------------------------------------------
// 4. ARTICLE DETAILS: Page Loader
// ---------------------------------------------------------
export async function initPostDetailPage() {
  const urlParams = new URLSearchParams(window.location.search);
  const slug = urlParams.get("slug");

  const container = document.getElementById("article-detail-container");
  if (!slug) {
    if (container) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⚠️</div>
          <h2 class="empty-state-title">Article Not Specified</h2>
          <p class="empty-state-desc">No post slug was provided in the URL.</p>
          <a href="../index.html" class="btn btn-primary btn-sm">Return to Home</a>
        </div>
      `;
    }
    return;
  }

  try {
    const res = await window.api.get(`/posts/slug/${encodeURIComponent(slug)}`);
    if (!res || !res.success || !res.data) {
      throw new Error((res && res.message) || "Article not found");
    }

    const post = res.data;
    document.title = `${post.title} — BlogSphere`;

    // Render breadcrumbs
    const breadcrumbCategory = document.getElementById("breadcrumb-category");
    const breadcrumbTitle = document.getElementById("breadcrumb-title");
    if (breadcrumbCategory) breadcrumbCategory.textContent = post.category ? post.category.name : "Articles";
    if (breadcrumbTitle) breadcrumbTitle.textContent = post.title;

    // Render Article
    renderArticleContent(post);

    // Load Related Posts
    loadRelatedPosts(post.id);

    // Load Comments
    loadComments(post.id);

    // Setup Comments Form
    setupCommentForm(post.id);

    // Setup Social Sharing
    setupSocialShare(post);
  } catch (err) {
    if (container) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📄</div>
          <h2 class="empty-state-title">Post not found</h2>
          <p class="empty-state-desc">The article you're looking for doesn't exist or may have been removed.</p>
          <a href="../index.html" class="btn btn-primary btn-sm">Back to Home</a>
        </div>
      `;
    }
  }
}

function renderArticleContent(post) {
  const container = document.getElementById("article-detail-container");
  if (!container) return;

  const defaultImg = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80";
  const authorAvatar = (post.author && post.author.profile_image) || getAssetPath("default-avatar.svg");

  const tagsHtml = (post.tags || [])
    .map((t) => `<a href="../index.html?tag=${encodeURIComponent(t.slug)}" class="tag-badge" style="font-size: 0.88rem; padding: 0.35rem 0.85rem;">#${t.name}</a>`)
    .join("");

  const updatedDateNotice = post.updated_at && post.updated_at !== post.published_at
    ? `<span>(Updated: ${window.formatDate(post.updated_at)})</span>`
    : "";

  container.innerHTML = `
    <header class="article-header">
      <span class="category-badge" style="margin-bottom: 1rem;">${post.category ? post.category.name : "Article"}</span>
      <h1 class="article-title">${post.title}</h1>
      ${post.excerpt ? `<p class="article-subtitle">${post.excerpt}</p>` : ""}
      
      <div class="article-meta-bar">
        <div class="author-chip">
          <img src="${authorAvatar}" alt="${post.author ? post.author.name : "Author"}" class="author-chip-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(post.author ? post.author.name : "A")}&background=4f46e5&color=fff'" />
          <div style="text-align: left;">
            <div class="author-chip-name">${post.author ? post.author.name : "Author"}</div>
            <div class="author-chip-date">${window.formatDate(post.published_at || post.created_at)} ${updatedDateNotice}</div>
          </div>
        </div>
        <div style="display: flex; gap: 1.25rem; font-size: 0.88rem; color: var(--text-muted);">
          <span>⏱️ ${post.reading_time_minutes || 1} min read</span>
          <span>👁️ ${post.views_count || 1} views</span>
        </div>
      </div>
    </header>

    ${post.featured_image ? `<img src="${post.featured_image}" alt="${post.title}" class="article-featured-img" onerror="this.src='${defaultImg}'" />` : ""}

    <div class="reading-container">
      <div class="prose" id="article-body-prose">
        ${post.content}
      </div>

      <div class="article-footer">
        <div class="tag-list" style="margin-bottom: 0;">
          ${tagsHtml}
        </div>
        <div class="share-buttons">
          <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-right: 0.5rem;">Share:</span>
          <button class="btn btn-outline btn-sm" id="btn-share-x" title="Share on X">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            X
          </button>
          <button class="btn btn-outline btn-sm" id="btn-share-linkedin" title="Share on LinkedIn">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
            LinkedIn
          </button>
          <button class="btn btn-outline btn-sm" id="btn-share-copy" title="Copy Link to Clipboard">
            🔗 Copy Link
          </button>
        </div>
      </div>

      <!-- Author Bio Box -->
      <div class="author-bio-card">
        <img src="${authorAvatar}" alt="${post.author ? post.author.name : "Author"}" class="author-bio-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(post.author ? post.author.name : "A")}&background=4f46e5&color=fff'" />
        <div>
          <div class="author-bio-name">Written by ${post.author ? post.author.name : "Author"}</div>
          <div class="author-bio-text">${(post.author && post.author.bio) || "Writer and contributor at BlogSphere."}</div>
        </div>
      </div>
    </div>
  `;
}

// ---------------------------------------------------------
// 5. Social Sharing Handlers
// ---------------------------------------------------------
function setupSocialShare(post) {
  const xBtn = document.getElementById("btn-share-x");
  const inBtn = document.getElementById("btn-share-linkedin");
  const copyBtn = document.getElementById("btn-share-copy");
  const fullUrl = encodeURIComponent(window.location.href);
  const title = encodeURIComponent(post.title);

  if (xBtn) {
    xBtn.onclick = () => {
      window.open(`https://twitter.com/intent/tweet?url=${fullUrl}&text=${title}`, "_blank", "width=600,height=400");
    };
  }

  if (inBtn) {
    inBtn.onclick = () => {
      window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${fullUrl}`, "_blank", "width=600,height=400");
    };
  }

  if (copyBtn) {
    copyBtn.onclick = () => {
      window.copyToClipboard(window.location.href, "Post link copied to clipboard!");
    };
  }
}

// ---------------------------------------------------------
// 6. Related Posts Loader
// ---------------------------------------------------------
async function loadRelatedPosts(postId) {
  const container = document.getElementById("related-posts-grid");
  if (!container) return;

  try {
    const res = await window.api.get(`/posts/${postId}/related?limit=3`);
    if (res && res.success && res.data && res.data.length > 0) {
      container.innerHTML = res.data.map((p) => renderPostCard(p)).join("");
      document.getElementById("related-posts-section").style.display = "block";
    } else {
      document.getElementById("related-posts-section").style.display = "none";
    }
  } catch (err) {
    console.warn("Could not load related posts:", err);
  }
}

// ---------------------------------------------------------
// 7. Comments Management
// ---------------------------------------------------------
async function loadComments(postId) {
  const commentsList = document.getElementById("comments-list");
  const commentsCountEl = document.getElementById("comments-count");
  if (!commentsList) return;

  try {
    const res = await window.api.get(`/posts/${postId}/comments`);
    if (res && res.success && res.data) {
      const comments = res.data;
      if (commentsCountEl) commentsCountEl.textContent = `(${comments.length})`;

      if (comments.length === 0) {
        commentsList.innerHTML = `<p style="color: var(--text-muted); font-size: 0.95rem; text-align: center; padding: 2rem 0;">No comments yet. Be the first to share your thoughts!</p>`;
        return;
      }

      commentsList.innerHTML = comments
        .map((c) => {
          const userAvatar = (c.user && c.user.profile_image) || getAssetPath("default-avatar.svg");
          const authorName = c.user ? c.user.name : c.guest_name || "Guest Reader";
          const isAuthor = c.user && c.user.role === "admin" ? `<span class="badge" style="background: var(--primary-light); color: var(--primary); font-size: 0.72rem; padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 700;">STAFF</span>` : "";

          return `
            <div class="comment-card" id="comment-${c.id}">
              <div class="comment-header">
                <div class="comment-author-info">
                  <img src="${userAvatar}" alt="${authorName}" class="comment-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(authorName)}&background=4f46e5&color=fff'" />
                  <div>
                    <span style="font-weight: 700; font-size: 0.92rem; color: var(--text-primary);">${authorName}</span>
                    ${isAuthor}
                    <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 0.5rem;">${window.formatRelativeTime(c.created_at)}</span>
                  </div>
                </div>
              </div>
              <div class="comment-content">${c.content}</div>
            </div>
          `;
        })
        .join("");
    }
  } catch (err) {
    console.warn("Could not load comments:", err);
  }
}

function setupCommentForm(postId) {
  const form = document.getElementById("comment-form");
  const guestFields = document.getElementById("guest-fields-container");
  if (!form) return;

  // Toggle guest inputs if authenticated
  if (window.auth && window.auth.isAuthenticated()) {
    if (guestFields) guestFields.style.display = "none";
  } else {
    if (guestFields) guestFields.style.display = "grid";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const contentInput = document.getElementById("comment-content");
    const nameInput = document.getElementById("guest-name");
    const emailInput = document.getElementById("guest-email");
    const submitBtn = document.getElementById("comment-submit-btn");

    const content = contentInput.value.trim();
    if (!content) {
      window.showToast("Please enter a comment message.", "warning");
      return;
    }

    const payload = { content };
    if (!window.auth || !window.auth.isAuthenticated()) {
      payload.guest_name = nameInput ? nameInput.value.trim() : "";
      payload.guest_email = emailInput && emailInput.value.trim() ? emailInput.value.trim() : null;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Posting...";
    }

    try {
      const res = await window.api.post(`/posts/${postId}/comments`, payload);
      if (res && res.success) {
        window.showToast("✓ Comment published successfully!", "success");
        contentInput.value = "";
        if (nameInput) nameInput.value = "";
        if (emailInput) emailInput.value = "";
        loadComments(postId);
      }
    } catch (err) {
      window.showToast(err.message || "Failed to submit comment", "error");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Post Comment";
      }
    }
  });
}

window.initHomePage = initHomePage;
window.initPostDetailPage = initPostDetailPage;
