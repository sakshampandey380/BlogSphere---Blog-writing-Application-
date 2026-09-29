/**
 * BlogSphere - Post Editor Engine (Create & Edit)
 * Formatting toolbar, live slug generator, tag chips, word count & preview
 */

let isEditMode = false;
let editingPostId = null;
let postTags = [];
let manualSlugEdited = false;

export async function initPostEditor() {
  if (!window.auth.requireAuth()) return;

  const urlParams = new URLSearchParams(window.location.search);
  editingPostId = urlParams.get("id");
  isEditMode = !!editingPostId;

  // 1. Load Categories
  await loadCategoriesDropdown();

  // 2. Setup Tag Chip Input
  setupTagChipsInput();

  // 3. Setup Formatting Toolbar
  setupFormattingToolbar();

  // 4. Setup Slug Auto-generator
  setupSlugGenerator();

  // 5. Setup Live Reading Time & Word Count
  setupLiveMetrics();

  // 6. Setup Preview Toggle
  setupPreviewTab();

  // 7. Setup Image URL preview
  setupImagePreview();

  // 8. If in Edit Mode, load post data
  if (isEditMode) {
    document.getElementById("editor-page-title").textContent = "Edit Article";
    document.getElementById("editor-breadcrumbs-current").textContent = "Edit Article";
    await loadExistingPost(editingPostId);
  }

  // 9. Setup Submit Handlers
  setupFormSubmission();
}

async function loadCategoriesDropdown() {
  const select = document.getElementById("post-category");
  if (!select) return;

  try {
    const res = await window.api.get("/categories");
    if (res && res.success && res.data) {
      let optionsHtml = `<option value="">Select a Category</option>`;
      res.data.forEach((c) => {
        optionsHtml += `<option value="${c.id}">${c.name}</option>`;
      });
      select.innerHTML = optionsHtml;
    }
  } catch (err) {
    console.warn("Could not load categories dropdown:", err);
  }
}

function setupSlugGenerator() {
  const titleInput = document.getElementById("post-title");
  const slugInput = document.getElementById("post-slug");

  if (!titleInput || !slugInput) return;

  titleInput.addEventListener("input", () => {
    if (!manualSlugEdited) {
      slugInput.value = generateSlug(titleInput.value);
    }
  });

  slugInput.addEventListener("input", () => {
    manualSlugEdited = true;
  });
}

function generateSlug(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function setupTagChipsInput() {
  const container = document.getElementById("tags-chip-container");
  const input = document.getElementById("tag-chip-input");
  if (!container || !input) return;

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTagFromInput(input.value);
      input.value = "";
    } else if (e.key === "Backspace" && !input.value && postTags.length > 0) {
      postTags.pop();
      renderTagChips();
    }
  });
}

function addTagFromInput(text) {
  const clean = text.replace(/,/g, "").trim();
  if (clean && !postTags.includes(clean)) {
    postTags.push(clean);
    renderTagChips();
  }
}

function renderTagChips() {
  const container = document.getElementById("tags-chip-container");
  const input = document.getElementById("tag-chip-input");
  if (!container || !input) return;

  // Clear existing chips before input
  const existingChips = container.querySelectorAll(".tag-chip");
  existingChips.forEach((c) => c.remove());

  postTags.forEach((tag, idx) => {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.innerHTML = `
      #${tag}
      <span class="tag-chip-remove" data-idx="${idx}" title="Remove tag">&times;</span>
    `;
    container.insertBefore(chip, input);
  });

  // Attach remove handlers
  container.querySelectorAll(".tag-chip-remove").forEach((btn) => {
    btn.onclick = () => {
      const idx = parseInt(btn.getAttribute("data-idx"), 10);
      postTags.splice(idx, 1);
      renderTagChips();
    };
  });
}

function setupFormattingToolbar() {
  const textarea = document.getElementById("post-content");
  if (!textarea) return;

  const tools = {
    bold: { wrap: ["**", "**"] },
    italic: { wrap: ["*", "*"] },
    h2: { prefix: "\n## " },
    h3: { prefix: "\n### " },
    quote: { prefix: "\n> " },
    code: { wrap: ["\n```javascript\n", "\n```\n"] },
    ul: { prefix: "\n- " },
    ol: { prefix: "\n1. " },
    link: { wrap: ["[", "](https://example.com)"] },
  };

  document.querySelectorAll(".editor-tool-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const toolType = btn.getAttribute("data-tool");
      const tool = tools[toolType];
      if (!tool) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const selectedText = textarea.value.substring(start, end);

      let replacement = "";
      if (tool.wrap) {
        replacement = `${tool.wrap[0]}${selectedText || "text"}${tool.wrap[1]}`;
      } else if (tool.prefix) {
        replacement = `${tool.prefix}${selectedText || "heading"}\n`;
      }

      textarea.focus();
      textarea.setRangeText(replacement, start, end, "end");
      updateLiveMetrics();
    });
  });
}

function setupLiveMetrics() {
  const textarea = document.getElementById("post-content");
  if (!textarea) return;
  textarea.addEventListener("input", updateLiveMetrics);
}

function updateLiveMetrics() {
  const textarea = document.getElementById("post-content");
  const wordsEl = document.getElementById("editor-word-count");
  const readingEl = document.getElementById("editor-reading-time");
  if (!textarea) return;

  const text = textarea.value.trim();
  const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
  const minutes = Math.max(1, Math.ceil(words / 200));

  if (wordsEl) wordsEl.textContent = `${words} words`;
  if (readingEl) readingEl.textContent = `⏱️ ${minutes} min read`;
}

function setupPreviewTab() {
  const writeTab = document.getElementById("tab-editor-write");
  const previewTab = document.getElementById("tab-editor-preview");
  const editorArea = document.getElementById("editor-textarea-wrapper");
  const previewArea = document.getElementById("editor-preview-wrapper");

  if (!writeTab || !previewTab || !editorArea || !previewArea) return;

  writeTab.addEventListener("click", () => {
    writeTab.classList.add("active");
    previewTab.classList.remove("active");
    editorArea.style.display = "block";
    previewArea.style.display = "none";
  });

  previewTab.addEventListener("click", () => {
    previewTab.classList.add("active");
    writeTab.classList.remove("active");
    editorArea.style.display = "none";
    previewArea.style.display = "block";

    // Simple markdown-to-HTML parser for preview
    const rawContent = document.getElementById("post-content").value;
    previewArea.innerHTML = parseMarkdownToHtml(rawContent);
  });
}

function parseMarkdownToHtml(md) {
  if (!md) return "<p><em>Nothing to preview yet. Start typing your thoughts!</em></p>";
  let html = md
    // Headings
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    // Blockquotes
    .replace(/^\> (.*$)/gim, "<blockquote>$1</blockquote>")
    // Code block
    .replace(/```([a-z]*)\n([\s\S]*?)```/gim, "<pre><code>$2</code></pre>")
    // Inline code
    .replace(/`([^`]+)`/gim, "<code>$1</code>")
    // Bold / Italic
    .replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/gim, "<em>$1</em>")
    // Links
    .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" target="_blank">$1</a>')
    // Unordered lists
    .replace(/^\- (.*$)/gim, "<li>$1</li>")
    // Paragraphs
    .replace(/\n\n/gim, "</p><p>");

  return `<p>${html}</p>`;
}

function setupImagePreview() {
  const imgInput = document.getElementById("post-featured-image");
  const imgPreview = document.getElementById("featured-image-preview");
  if (!imgInput || !imgPreview) return;

  imgInput.addEventListener("input", () => {
    const url = imgInput.value.trim();
    if (url) {
      imgPreview.src = url;
      imgPreview.style.display = "block";
      imgPreview.onerror = () => {
        imgPreview.style.display = "none";
      };
    } else {
      imgPreview.style.display = "none";
    }
  });
}

async function loadExistingPost(id) {
  try {
    const res = await window.api.get(`/posts/${id}`);
    if (!res || !res.success || !res.data) {
      throw new Error("Unable to load post details for editing.");
    }

    const post = res.data;
    const currentUser = window.auth.getUser();

    // Check permissions
    if (post.author.id !== currentUser.id && currentUser.role !== "admin") {
      alert("Access Denied: You do not have permission to edit this article.");
      window.location.href = "dashboard.html";
      return;
    }

    document.getElementById("post-title").value = post.title || "";
    document.getElementById("post-slug").value = post.slug || "";
    manualSlugEdited = true;

    if (post.category) {
      document.getElementById("post-category").value = post.category.id;
    }

    document.getElementById("post-excerpt").value = post.excerpt || "";
    document.getElementById("post-content").value = post.content || "";
    document.getElementById("post-featured-image").value = post.featured_image || "";
    document.getElementById("post-is-featured").checked = !!post.is_featured;

    if (post.featured_image) {
      const preview = document.getElementById("featured-image-preview");
      if (preview) {
        preview.src = post.featured_image;
        preview.style.display = "block";
      }
    }

    // Set tags
    postTags = (post.tags || []).map((t) => t.name);
    renderTagChips();
    updateLiveMetrics();
  } catch (err) {
    window.showToast(err.message, "error");
  }
}

function setupFormSubmission() {
  const form = document.getElementById("post-editor-form");
  const saveDraftBtn = document.getElementById("btn-save-draft");
  const publishBtn = document.getElementById("btn-publish-post");

  if (!form) return;

  const submitPost = async (targetStatus) => {
    const title = document.getElementById("post-title").value.trim();
    const slug = document.getElementById("post-slug").value.trim();
    const categoryId = document.getElementById("post-category").value;
    const excerpt = document.getElementById("post-excerpt").value.trim();
    const content = document.getElementById("post-content").value.trim();
    const featuredImage = document.getElementById("post-featured-image").value.trim();
    const isFeatured = document.getElementById("post-is-featured").checked;

    // Validate
    const titleErr = window.validateTitle(title);
    if (titleErr) {
      window.showToast(titleErr, "warning");
      document.getElementById("post-title").focus();
      return;
    }

    if (targetStatus === "published") {
      const contentErr = window.validateContent(content);
      if (contentErr) {
        window.showToast(contentErr, "warning");
        document.getElementById("post-content").focus();
        return;
      }
    }

    const payload = {
      title,
      slug: slug || generateSlug(title),
      category_id: categoryId ? parseInt(categoryId, 10) : null,
      excerpt: excerpt || null,
      content: content || "<p>Draft notes</p>",
      featured_image: featuredImage || null,
      tags: postTags,
      status: targetStatus,
      is_featured: isFeatured,
    };

    saveDraftBtn.disabled = true;
    publishBtn.disabled = true;
    const activeBtn = targetStatus === "published" ? publishBtn : saveDraftBtn;
    activeBtn.textContent = "Saving...";

    try {
      let res;
      if (isEditMode) {
        res = await window.api.put(`/posts/${editingPostId}`, payload);
      } else {
        res = await window.api.post("/posts", payload);
      }

      if (res && res.success && res.data) {
        const savedPost = res.data;
        window.showToast(`✓ Post ${targetStatus === "published" ? "published" : "saved as draft"} successfully!`, "success");

        setTimeout(() => {
          if (targetStatus === "published") {
            window.location.href = `post.html?slug=${encodeURIComponent(savedPost.slug)}`;
          } else {
            window.location.href = "dashboard.html";
          }
        }, 800);
      }
    } catch (err) {
      window.showToast(err.message || "Failed to save article", "error");
      saveDraftBtn.disabled = false;
      publishBtn.disabled = false;
      saveDraftBtn.textContent = "Save Draft";
      publishBtn.textContent = "Publish Post";
    }
  };

  saveDraftBtn.addEventListener("click", () => submitPost("draft"));
  publishBtn.addEventListener("click", () => submitPost("published"));
}

window.initPostEditor = initPostEditor;
