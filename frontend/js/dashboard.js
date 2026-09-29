/**
 * BlogSphere - User & Author Dashboard Logic
 */

let currentTab = "all";
let currentScope = "mine";
let dashboardSearch = "";

export async function initDashboard() {
  if (!window.auth.requireAuth()) return;

  const user = window.auth.getUser();
  const welcomeEl = document.getElementById("dashboard-welcome-name");
  if (welcomeEl && user) {
    welcomeEl.textContent = user.name;
  }

  // If user is admin, show admin scope toggle tab
  const adminScopeTab = document.getElementById("admin-scope-toggle");
  if (adminScopeTab && user && user.role === "admin") {
    adminScopeTab.style.display = "flex";
    adminScopeTab.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        adminScopeTab.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentScope = btn.getAttribute("data-scope");
        loadDashboardPosts();
      });
    });
  }

  // Setup Status Filter Tabs
  const statusTabs = document.querySelectorAll(".dashboard-tab-btn");
  statusTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      statusTabs.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentTab = btn.getAttribute("data-status");
      loadDashboardPosts();
    });
  });

  // Setup Dashboard Search
  const searchInput = document.getElementById("dashboard-search-input");
  if (searchInput) {
    let timeout;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        dashboardSearch = e.target.value.trim();
        loadDashboardPosts();
      }, 300);
    });
  }

  // Load metrics & posts
  await Promise.all([loadDashboardStats(), loadDashboardPosts()]);
}

// ---------------------------------------------------------
// 1. Load Metrics Cards
// ---------------------------------------------------------
async function loadDashboardStats() {
  try {
    const res = await window.api.get("/dashboard/stats");
    if (!res || !res.success || !res.data) return;

    const stats = res.data.user_stats;
    document.getElementById("stat-total-posts").textContent = stats.total_posts || 0;
    document.getElementById("stat-published-posts").textContent = stats.published_posts || 0;
    document.getElementById("stat-draft-posts").textContent = stats.draft_posts || 0;
    document.getElementById("stat-total-views").textContent = stats.total_views || 0;

    // Admin platform banner if available
    const adminBanner = document.getElementById("admin-platform-stats");
    if (adminBanner && res.data.admin_stats) {
      const a = res.data.admin_stats;
      adminBanner.innerHTML = `
        <div style="background: var(--bg-card); border: 1px solid var(--border-default); border-left: 4px solid var(--primary); border-radius: var(--radius-md); padding: 1rem 1.5rem; margin-bottom: 2rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
          <div>
            <div style="font-weight: 700; color: var(--text-primary);">🛡️ Administrative Platform Overview</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">Global system metrics across all registered authors</div>
          </div>
          <div style="display: flex; gap: 1.5rem; font-size: 0.92rem;">
            <span>👥 <strong>${a.site_users_count}</strong> Authors</span>
            <span>📝 <strong>${a.site_total_posts}</strong> Articles (${a.site_published_posts} pub / ${a.site_draft_posts} draft)</span>
            <span>👁️ <strong>${a.site_views_count}</strong> Views</span>
          </div>
        </div>
      `;
      adminBanner.style.display = "block";
    }
  } catch (err) {
    console.warn("Failed to load dashboard metrics:", err);
  }
}

// ---------------------------------------------------------
// 2. Load User / System Posts Table
// ---------------------------------------------------------
async function loadDashboardPosts() {
  const tableBody = document.getElementById("dashboard-posts-table-body");
  if (!tableBody) return;

  tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem;"><div class="skeleton" style="height: 30px; width: 80%; margin: 0 auto;"></div></td></tr>`;

  try {
    const params = {
      scope: currentScope,
      status: currentTab,
      search: dashboardSearch,
    };

    const res = await window.api.get("/dashboard/posts", params);
    if (!res || !res.success || !res.data) {
      throw new Error("Unable to fetch dashboard posts.");
    }

    const posts = res.data;

    if (posts.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: 3.5rem 1rem;">
            <div class="empty-state" style="padding: 1.5rem; border: none; box-shadow: none;">
              <div class="empty-state-icon">✍️</div>
              <h4 class="empty-state-title">No articles found</h4>
              <p class="empty-state-desc">You haven't created any posts in this view yet.</p>
              <a href="create-post.html" class="btn btn-primary btn-sm">+ Create Your First Post</a>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = posts.map((p) => renderDashboardRow(p)).join("");

    // Attach row action listeners
    attachDashboardRowActions();
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--danger); padding: 2rem;">${err.message}</td></tr>`;
  }
}

function renderDashboardRow(post) {
  const isPublished = post.status === "published";
  const statusBadge = isPublished
    ? `<span class="status-badge status-published">● Published</span>`
    : `<span class="status-badge status-draft">○ Draft</span>`;

  const toggleActionText = isPublished ? "Unpublish" : "Publish";
  const toggleActionIcon = isPublished ? "⏸️" : "🚀";

  return `
    <tr id="dashboard-row-${post.id}">
      <td>
        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.95rem;">
          <a href="post.html?slug=${encodeURIComponent(post.slug)}" target="_blank" style="color: inherit;">${post.title}</a>
        </div>
        <div style="font-size: 0.78rem; color: var(--text-muted);">
          /${post.slug}
          ${post.author && currentScope === "all" ? ` • By ${post.author.name}` : ""}
        </div>
      </td>
      <td>
        <span class="category-badge" style="font-size: 0.75rem;">${post.category ? post.category.name : "Unassigned"}</span>
      </td>
      <td>${statusBadge}</td>
      <td><strong>${post.views_count || 0}</strong></td>
      <td style="font-size: 0.82rem; color: var(--text-muted);">${window.formatDate(post.created_at)}</td>
      <td>
        <div style="display: flex; gap: 0.4rem; justify-content: flex-end;">
          <a href="post.html?slug=${encodeURIComponent(post.slug)}" target="_blank" class="btn btn-icon btn-sm" title="View Public Post">
            👁️
          </a>
          <a href="edit-post.html?id=${post.id}" class="btn btn-icon btn-sm" title="Edit Article">
            ✏️
          </a>
          <button class="btn btn-icon btn-sm btn-toggle-status" data-id="${post.id}" data-action="${isPublished ? "unpublish" : "publish"}" title="${toggleActionText}">
            ${toggleActionIcon}
          </button>
          <button class="btn btn-icon btn-sm btn-delete-post" data-id="${post.id}" data-title="${encodeURIComponent(post.title)}" title="Delete Post" style="color: var(--danger);">
            🗑️
          </button>
        </div>
      </td>
    </tr>
  `;
}

function attachDashboardRowActions() {
  // 1. Publish / Unpublish Toggle
  document.querySelectorAll(".btn-toggle-status").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const postId = btn.getAttribute("data-id");
      const action = btn.getAttribute("data-action");

      btn.disabled = true;
      try {
        const res = await window.api.patch(`/posts/${postId}/${action}`);
        if (res && res.success) {
          window.showToast(`✓ Post ${action === "publish" ? "published" : "unpublished"} successfully!`, "success");
          loadDashboardStats();
          loadDashboardPosts();
        }
      } catch (err) {
        window.showToast(err.message || `Unable to ${action} post`, "error");
        btn.disabled = false;
      }
    });
  });

  // 2. Delete Post with Confirmation Modal
  document.querySelectorAll(".btn-delete-post").forEach((btn) => {
    btn.addEventListener("click", () => {
      const postId = btn.getAttribute("data-id");
      const postTitle = decodeURIComponent(btn.getAttribute("data-title"));

      window.showConfirmModal({
        title: "Delete Article?",
        message: `Are you sure you want to permanently delete "<strong>${postTitle}</strong>"? This action cannot be undone.`,
        confirmText: "Delete Permanently",
        cancelText: "Cancel",
        isDestructive: true,
        onConfirm: async () => {
          try {
            const res = await window.api.delete(`/posts/${postId}`);
            if (res && res.success) {
              window.showToast("✓ Post deleted successfully.", "success");
              loadDashboardStats();
              loadDashboardPosts();
            }
          } catch (err) {
            window.showToast(err.message || "Failed to delete post", "error");
          }
        },
      });
    });
  });
}

window.initDashboard = initDashboard;
