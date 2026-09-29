/**
 * BlogSphere - Administration Portal Engine
 * Users, Categories, and Tags Management
 */

export async function initAdminPortal() {
  if (!window.auth.requireAdmin()) return;

  // Setup Tabs
  const tabs = document.querySelectorAll(".admin-tab-btn");
  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabs.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const target = btn.getAttribute("data-tab");
      document.querySelectorAll(".admin-tab-panel").forEach((panel) => {
        panel.style.display = panel.id === `panel-${target}` ? "block" : "none";
      });
    });
  });

  // Load Initial Panels
  await Promise.all([loadAdminUsers(), loadAdminCategories(), loadAdminTags()]);

  // Setup Category creation form
  setupCategoryCreation();
}

// ---------------------------------------------------------
// 1. Users Management
// ---------------------------------------------------------
async function loadAdminUsers() {
  const tbody = document.getElementById("admin-users-table-body");
  if (!tbody) return;

  try {
    const res = await window.api.get("/users");
    if (!res || !res.success || !res.data) return;

    const users = res.data;
    const currentUser = window.auth.getUser();

    tbody.innerHTML = users
      .map((u) => {
        const isSelf = u.id === currentUser.id;
        const statusBadge = u.is_active
          ? `<span class="status-badge status-published">Active</span>`
          : `<span class="status-badge status-draft">Inactive</span>`;

        return `
          <tr>
            <td>
              <div style="font-weight: 700; color: var(--text-primary);">${u.name} ${isSelf ? '<span style="font-size:0.75rem; color:var(--primary);">(You)</span>' : ""}</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">${u.email}</div>
            </td>
            <td>
              <span class="category-badge" style="font-size: 0.72rem; ${u.role === "admin" ? "background:var(--primary); color:#fff;" : ""}">${u.role}</span>
            </td>
            <td>${statusBadge}</td>
            <td>${u.posts_count || 0}</td>
            <td style="font-size: 0.82rem; color: var(--text-muted);">${window.formatDate(u.created_at)}</td>
            <td>
              <div style="display: flex; gap: 0.4rem; justify-content: flex-end;">
                ${
                  !isSelf
                    ? `
                  <button class="btn btn-outline btn-sm btn-toggle-user-role" data-id="${u.id}" data-role="${u.role === "admin" ? "user" : "admin"}" title="Toggle Role">
                    ${u.role === "admin" ? "Demote to User" : "Promote to Admin"}
                  </button>
                  <button class="btn btn-sm ${u.is_active ? "btn-danger" : "btn-secondary"} btn-toggle-user-status" data-id="${u.id}" data-active="${u.is_active}">
                    ${u.is_active ? "Deactivate" : "Activate"}
                  </button>
                `
                    : '<span style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">Protected</span>'
                }
              </div>
            </td>
          </tr>
        `;
      })
      .join("");

    // Attach User Actions
    tbody.querySelectorAll(".btn-toggle-user-status").forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-id");
        try {
          const res = await window.api.patch(`/users/${id}/status`);
          if (res && res.success) {
            window.showToast("✓ User status updated successfully", "success");
            loadAdminUsers();
          }
        } catch (err) {
          window.showToast(err.message, "error");
        }
      };
    });

    tbody.querySelectorAll(".btn-toggle-user-role").forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-id");
        const newRole = btn.getAttribute("data-role");
        try {
          const res = await window.api.patch(`/users/${id}/role?new_role=${newRole}`);
          if (res && res.success) {
            window.showToast(`✓ User role changed to ${newRole}`, "success");
            loadAdminUsers();
          }
        } catch (err) {
          window.showToast(err.message, "error");
        }
      };
    });
  } catch (err) {
    console.error("Failed to load admin users:", err);
  }
}

// ---------------------------------------------------------
// 2. Categories Management
// ---------------------------------------------------------
async function loadAdminCategories() {
  const tbody = document.getElementById("admin-categories-table-body");
  if (!tbody) return;

  try {
    const res = await window.api.get("/categories");
    if (!res || !res.success || !res.data) return;

    const categories = res.data;

    tbody.innerHTML = categories
      .map(
        (c) => `
        <tr>
          <td>
            <strong>${c.name}</strong>
          </td>
          <td><code>${c.slug}</code></td>
          <td style="font-size: 0.85rem; color: var(--text-muted);">${c.description || "—"}</td>
          <td><strong>${c.posts_count || 0}</strong></td>
          <td>
            <div style="display: flex; gap: 0.4rem; justify-content: flex-end;">
              <button class="btn btn-icon btn-sm btn-delete-category" data-id="${c.id}" data-name="${c.name}" title="Delete Category" style="color: var(--danger);">
                🗑️
              </button>
            </div>
          </td>
        </tr>
      `
      )
      .join("");

    tbody.querySelectorAll(".btn-delete-category").forEach((btn) => {
      btn.onclick = () => {
        const id = btn.getAttribute("data-id");
        const name = btn.getAttribute("data-name");

        window.showConfirmModal({
          title: "Delete Category?",
          message: `Are you sure you want to delete the category "<strong>${name}</strong>"? Posts in this category will remain, but will have their category unassigned.`,
          confirmText: "Delete",
          isDestructive: true,
          onConfirm: async () => {
            try {
              const res = await window.api.delete(`/categories/${id}`);
              if (res && res.success) {
                window.showToast("✓ Category deleted successfully", "success");
                loadAdminCategories();
              }
            } catch (err) {
              window.showToast(err.message, "error");
            }
          },
        });
      };
    });
  } catch (err) {
    console.error("Failed to load admin categories:", err);
  }
}

function setupCategoryCreation() {
  const form = document.getElementById("create-category-form");
  if (!form) return;

  form.onsubmit = async (e) => {
    e.preventDefault();
    const nameInput = document.getElementById("category-name-input");
    const descInput = document.getElementById("category-desc-input");
    const submitBtn = document.getElementById("create-category-btn");

    const name = nameInput.value.trim();
    const description = descInput.value.trim();

    if (!name) {
      window.showToast("Category name is required", "warning");
      return;
    }

    submitBtn.disabled = true;
    try {
      const res = await window.api.post("/categories", { name, description });
      if (res && res.success) {
        window.showToast("✓ Category created successfully!", "success");
        nameInput.value = "";
        descInput.value = "";
        loadAdminCategories();
      }
    } catch (err) {
      window.showToast(err.message || "Failed to create category", "error");
    } finally {
      submitBtn.disabled = false;
    }
  };
}

// ---------------------------------------------------------
// 3. Tags Management
// ---------------------------------------------------------
async function loadAdminTags() {
  const container = document.getElementById("admin-tags-container");
  if (!container) return;

  try {
    const res = await window.api.get("/tags");
    if (!res || !res.success || !res.data) return;

    const tags = res.data;

    container.innerHTML = tags
      .map(
        (t) => `
        <span class="tag-chip" style="font-size: 0.9rem; padding: 0.35rem 0.75rem;">
          #${t.name} (${t.posts_count || 0})
          <span class="tag-chip-remove btn-delete-tag" data-id="${t.id}" data-name="${t.name}" title="Delete tag">&times;</span>
        </span>
      `
      )
      .join("");

    container.querySelectorAll(".btn-delete-tag").forEach((btn) => {
      btn.onclick = () => {
        const id = btn.getAttribute("data-id");
        const name = btn.getAttribute("data-name");

        window.showConfirmModal({
          title: "Delete Tag?",
          message: `Delete tag "<strong>#${name}</strong>"?`,
          confirmText: "Delete",
          isDestructive: true,
          onConfirm: async () => {
            try {
              const res = await window.api.delete(`/tags/${id}`);
              if (res && res.success) {
                window.showToast("✓ Tag deleted", "success");
                loadAdminTags();
              }
            } catch (err) {
              window.showToast(err.message, "error");
            }
          },
        });
      };
    });
  } catch (err) {
    console.error("Failed to load tags:", err);
  }
}

window.initAdminPortal = initAdminPortal;
