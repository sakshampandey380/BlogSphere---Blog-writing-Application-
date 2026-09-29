/**
 * BlogSphere - UI Components & Utility Helpers
 * Toasts, Modals, Theme Switcher, Date Formatters, Skeleton Loaders
 */

// ---------------------------------------------------------
// 1. Toast Notification System
// ---------------------------------------------------------
function getToastContainer() {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  return container;
}

export function showToast(message, type = "success", duration = 3500) {
  const container = getToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const icons = {
    success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
    error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
    warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
    info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

// ---------------------------------------------------------
// 2. Accessible Confirmation Modal
// ---------------------------------------------------------
export function showConfirmModal({
  title = "Confirm Action",
  message = "Are you sure you want to proceed?",
  confirmText = "Confirm",
  cancelText = "Cancel",
  isDestructive = false,
  onConfirm = () => {},
}) {
  let modalOverlay = document.getElementById("confirm-modal-overlay");
  if (!modalOverlay) {
    modalOverlay = document.createElement("div");
    modalOverlay.id = "confirm-modal-overlay";
    modalOverlay.className = "modal-overlay";
    document.body.appendChild(modalOverlay);
  }

  const confirmBtnClass = isDestructive ? "btn-danger" : "btn-primary";

  modalOverlay.innerHTML = `
    <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal-header">
        <h4 class="modal-title" id="modal-title">${title}</h4>
        <button class="btn-icon btn-sm" id="modal-close-btn" aria-label="Close modal">✕</button>
      </div>
      <div class="modal-body">
        <p>${message}</p>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary btn-sm" id="modal-cancel-btn">${cancelText}</button>
        <button class="btn ${confirmBtnClass} btn-sm" id="modal-confirm-btn">${confirmText}</button>
      </div>
    </div>
  `;

  modalOverlay.classList.add("show");

  const close = () => {
    modalOverlay.classList.remove("show");
  };

  document.getElementById("modal-close-btn").onclick = close;
  document.getElementById("modal-cancel-btn").onclick = close;
  document.getElementById("modal-confirm-btn").onclick = () => {
    close();
    onConfirm();
  };

  modalOverlay.onclick = (e) => {
    if (e.target === modalOverlay) close();
  };
}

// ---------------------------------------------------------
// 3. Theme Manager (Light / Dark / System)
// ---------------------------------------------------------
export function initThemeManager() {
  const savedTheme = localStorage.getItem("blogsphere_theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initialTheme = savedTheme || (prefersDark ? "dark" : "light");

  applyTheme(initialTheme);

  // Update theme toggles on page
  const toggles = document.querySelectorAll(".theme-toggle-btn");
  toggles.forEach((btn) => {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      localStorage.setItem("blogsphere_theme", next);
    });
  });

  // Listen for system changes if no override
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    if (!localStorage.getItem("blogsphere_theme")) {
      applyTheme(e.matches ? "dark" : "light");
    }
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const toggles = document.querySelectorAll(".theme-toggle-btn");
  toggles.forEach((btn) => {
    if (theme === "dark") {
      btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
      btn.setAttribute("title", "Switch to Light Mode");
    } else {
      btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
      btn.setAttribute("title", "Switch to Dark Mode");
    }
  });
}

// ---------------------------------------------------------
// 4. Date & Time Formatters
// ---------------------------------------------------------
export function formatDate(dateString) {
  if (!dateString) return "Recently";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeTime(dateString) {
  if (!dateString) return "Recently";
  const date = new Date(dateString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return "Just now";
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;

  return formatDate(dateString);
}

// ---------------------------------------------------------
// 5. Clipboard & Share Helpers
// ---------------------------------------------------------
export function copyToClipboard(text, customMsg = "Link copied to clipboard!") {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(`✓ ${customMsg}`, "success");
    }).catch(() => fallbackCopy(text, customMsg));
  } else {
    fallbackCopy(text, customMsg);
  }
}

function fallbackCopy(text, customMsg) {
  const el = document.createElement("textarea");
  el.value = text;
  document.body.appendChild(el);
  el.select();
  document.execCommand("copy");
  document.body.removeChild(el);
  showToast(`✓ ${customMsg}`, "success");
}

// ---------------------------------------------------------
// 6. Skeleton Loader Generator
// ---------------------------------------------------------
export function renderCardSkeleton(count = 3) {
  let html = "";
  for (let i = 0; i < count; i++) {
    html += `
      <div class="skeleton-card">
        <div class="skeleton" style="height: 190px; width: 100%;"></div>
        <div style="padding: 1.5rem; display: flex; flex-direction: column; gap: 0.85rem;">
          <div class="skeleton" style="height: 16px; width: 35%;"></div>
          <div class="skeleton" style="height: 24px; width: 90%;"></div>
          <div class="skeleton" style="height: 16px; width: 100%;"></div>
          <div class="skeleton" style="height: 16px; width: 75%;"></div>
          <div style="margin-top: 1rem; display: flex; gap: 0.75rem; align-items: center;">
            <div class="skeleton" style="height: 32px; width: 32px; border-radius: 50%;"></div>
            <div class="skeleton" style="height: 16px; width: 40%;"></div>
          </div>
        </div>
      </div>
    `;
  }
  return html;
}

// Attach helpers to window for easy access across all page scripts
window.showToast = showToast;
window.showConfirmModal = showConfirmModal;
window.formatDate = formatDate;
window.formatRelativeTime = formatRelativeTime;
window.copyToClipboard = copyToClipboard;
window.renderCardSkeleton = renderCardSkeleton;
window.initThemeManager = initThemeManager;

document.addEventListener("DOMContentLoaded", () => {
  initThemeManager();

  // Mobile navigation drawer toggle
  const mobileToggle = document.getElementById("mobile-nav-toggle");
  const navLinks = document.getElementById("nav-links");
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener("click", () => {
      navLinks.classList.toggle("show");
    });
  }
});
