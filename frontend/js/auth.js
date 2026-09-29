/**
 * BlogSphere - Authentication & Session Manager
 */

class AuthManager {
  constructor() {
    this.user = this.loadUser();
  }

  loadUser() {
    try {
      const data = localStorage.getItem("blogsphere_user");
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  }

  saveSession(token, user) {
    if (token) localStorage.setItem("blogsphere_token", token);
    if (user) {
      localStorage.setItem("blogsphere_user", JSON.stringify(user));
      this.user = user;
    }
    window.dispatchEvent(new Event("auth_state_changed"));
  }

  clearSession() {
    localStorage.removeItem("blogsphere_token");
    localStorage.removeItem("blogsphere_user");
    this.user = null;
    window.dispatchEvent(new Event("auth_state_changed"));
  }

  getUser() {
    return this.user || this.loadUser();
  }

  isAuthenticated() {
    return !!localStorage.getItem("blogsphere_token");
  }

  isAdmin() {
    const user = this.getUser();
    return user && user.role === "admin";
  }

  async login(email, password) {
    const response = await window.api.post("/auth/login", { email, password });
    if (response && response.success && response.data) {
      this.saveSession(response.data.access_token, response.data.user);
      return response.data;
    }
    throw new Error((response && response.message) || "Authentication failed");
  }

  async register(name, email, password) {
    const response = await window.api.post("/auth/register", { name, email, password });
    if (response && response.success && response.data) {
      this.saveSession(response.data.access_token, response.data.user);
      return response.data;
    }
    throw new Error((response && response.message) || "Registration failed");
  }

  async logout() {
    try {
      await window.api.post("/auth/logout", {});
    } catch (e) {
      console.warn("Logout request ignored error:", e);
    } finally {
      this.clearSession();
      // Redirect to home page or login page
      const currentPath = window.location.pathname;
      if (currentPath.includes("dashboard") || currentPath.includes("create-post") || currentPath.includes("edit-post") || currentPath.includes("profile") || currentPath.includes("admin")) {
        window.location.href = window.location.origin + (window.location.port === "8000" ? "/" : window.location.pathname.replace(/\/pages\/.*/, "/index.html"));
      } else {
        window.location.reload();
      }
    }
  }

  async refreshUser() {
    if (!this.isAuthenticated()) return null;
    try {
      const response = await window.api.get("/auth/me");
      if (response && response.success && response.data && response.data.user) {
        this.saveSession(null, response.data.user);
        return response.data.user;
      }
    } catch {
      this.clearSession();
    }
    return null;
  }

  requireAuth(redirectUrl = null) {
    if (!this.isAuthenticated()) {
      const current = encodeURIComponent(window.location.href);
      const target = redirectUrl || (window.location.port === "8000" ? `/pages/login.html?redirect=${current}` : `./login.html?redirect=${current}`);
      window.location.href = target;
      return false;
    }
    return true;
  }

  requireAdmin(redirectUrl = null) {
    if (!this.requireAuth(redirectUrl)) return false;
    if (!this.isAdmin()) {
      alert("Access Denied: Administrative privileges required.");
      window.location.href = window.location.port === "8000" ? "/pages/dashboard.html" : "./dashboard.html";
      return false;
    }
    return true;
  }

  renderNavbarAuth() {
    const authContainer = document.getElementById("nav-auth-container");
    if (!authContainer) return;

    const user = this.getUser();
    const isRoot = window.location.pathname.endsWith("index.html") || window.location.pathname === "/" || window.location.pathname.endsWith("QSkills - Task -2/") || window.location.pathname.endsWith("frontend/");
    const basePath = isRoot ? (window.location.port === "8000" ? "/pages" : "./pages") : ".";

    if (user && this.isAuthenticated()) {
      const avatarSrc = user.profile_image || (isRoot ? (window.location.port === "8000" ? "/assets/default-avatar.svg" : "./assets/default-avatar.svg") : "../assets/default-avatar.svg");
      const adminLink = user.role === "admin" ? `<a href="${basePath}/admin.html" class="dropdown-item">⚙️ Admin Portal</a>` : "";

      authContainer.innerHTML = `
        <a href="${basePath}/create-post.html" class="btn btn-primary btn-sm" id="btn-create-post">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          Write Post
        </a>
        <div class="user-menu-wrapper">
          <button class="user-avatar-btn" id="user-menu-trigger" aria-haspopup="true" aria-expanded="false">
            <img src="${avatarSrc}" alt="${user.name}" class="user-avatar" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=4f46e5&color=fff'" />
            <span class="user-name-label">${user.name.split(" ")[0]}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <div class="user-dropdown" id="user-dropdown-menu">
            <div class="dropdown-header">
              <div class="dropdown-user-name">${user.name}</div>
              <div class="dropdown-user-role">${user.role}</div>
            </div>
            <a href="${basePath}/dashboard.html" class="dropdown-item">📊 My Dashboard</a>
            <a href="${basePath}/create-post.html" class="dropdown-item">✍️ New Article</a>
            <a href="${basePath}/profile.html" class="dropdown-item">👤 Profile & Settings</a>
            ${adminLink}
            <div style="border-top: 1px solid var(--border-subtle); margin: 0.35rem 0;"></div>
            <button class="dropdown-item danger" id="btn-logout">🚪 Sign Out</button>
          </div>
        </div>
      `;

      // Setup Dropdown toggle
      const trigger = document.getElementById("user-menu-trigger");
      const dropdown = document.getElementById("user-dropdown-menu");
      const logoutBtn = document.getElementById("btn-logout");

      if (trigger && dropdown) {
        trigger.addEventListener("click", (e) => {
          e.stopPropagation();
          dropdown.classList.toggle("show");
        });

        document.addEventListener("click", () => {
          dropdown.classList.remove("show");
        });
      }

      if (logoutBtn) {
        logoutBtn.addEventListener("click", () => this.logout());
      }
    } else {
      authContainer.innerHTML = `
        <a href="${basePath}/login.html" class="btn btn-outline btn-sm">Sign In</a>
        <a href="${basePath}/register.html" class="btn btn-primary btn-sm">Get Started</a>
      `;
    }
  }
}

const auth = new AuthManager();
window.auth = auth;

// Listen for session changes to re-render navbar automatically
window.addEventListener("auth_state_changed", () => {
  auth.renderNavbarAuth();
});

// Auto-render navbar on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  auth.renderNavbarAuth();
});
