/**
 * BlogSphere - Client-side Form Validation
 */

export function validateEmail(email) {
  if (!email || !email.trim()) return "Email address is required.";
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(email.trim())) return "Please enter a valid email address.";
  return null;
}

export function validatePassword(password, minLength = 6) {
  if (!password) return "Password is required.";
  if (password.length < minLength) return `Password must be at least ${minLength} characters.`;
  return null;
}

export function validateTitle(title) {
  if (!title || !title.trim()) return "Article title is required.";
  if (title.trim().length < 3) return "Title must be at least 3 characters long.";
  if (title.trim().length > 255) return "Title cannot exceed 255 characters.";
  return null;
}

export function validateContent(content) {
  if (!content || !content.trim()) return "Article content cannot be empty.";
  if (content.trim().length < 10) return "Content must be at least 10 characters long.";
  return null;
}

export function validateSlug(slug) {
  if (!slug || !slug.trim()) return "Slug is required.";
  const re = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  if (!re.test(slug.trim())) return "Slug may only contain lowercase letters, numbers, and hyphens.";
  return null;
}

export function setFieldError(inputEl, errorMsg) {
  if (!inputEl) return;
  inputEl.classList.add("input-error");
  const parent = inputEl.closest(".form-group") || inputEl.parentElement;
  let msgEl = parent.querySelector(".form-error-msg");
  if (!msgEl) {
    msgEl = document.createElement("div");
    msgEl.className = "form-error-msg";
    parent.appendChild(msgEl);
  }
  msgEl.textContent = errorMsg;
  msgEl.style.display = "block";
}

export function clearFieldError(inputEl) {
  if (!inputEl) return;
  inputEl.classList.remove("input-error");
  const parent = inputEl.closest(".form-group") || inputEl.parentElement;
  const msgEl = parent.querySelector(".form-error-msg");
  if (msgEl) {
    msgEl.textContent = "";
    msgEl.style.display = "none";
  }
}

window.validateEmail = validateEmail;
window.validatePassword = validatePassword;
window.validateTitle = validateTitle;
window.validateContent = validateContent;
window.validateSlug = validateSlug;
window.setFieldError = setFieldError;
window.clearFieldError = clearFieldError;
