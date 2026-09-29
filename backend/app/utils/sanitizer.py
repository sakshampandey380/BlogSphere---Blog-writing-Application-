from bs4 import BeautifulSoup

ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "b", "strong", "i", "em", "u", "s", "del", "mark",
    "blockquote", "code", "pre", "kbd",
    "ul", "ol", "li",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "hr", "br", "span", "div", "figure", "figcaption"
}

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel", "class"],
    "img": ["src", "alt", "title", "width", "height", "class", "loading"],
    "code": ["class"],
    "pre": ["class"],
    "span": ["class"],
    "div": ["class"],
    "p": ["class"],
    "table": ["class"],
    "th": ["class", "colspan", "rowspan"],
    "td": ["class", "colspan", "rowspan"],
}

SAFE_URL_SCHEMES = ("http://", "https://", "mailto:", "/", "#", "data:image/")


def sanitize_html(html_content: str) -> str:
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup.find_all(True):
        if tag.name.lower() not in ALLOWED_TAGS:
            tag.decompose()
            continue

        tag_name = tag.name.lower()
        allowed_attrs = ALLOWED_ATTRIBUTES.get(tag_name, [])

        attrs = dict(tag.attrs)
        for attr, value in attrs.items():
            attr_lower = attr.lower()

            if attr_lower.startswith("on"):
                del tag.attrs[attr]
                continue

            if attr_lower not in allowed_attrs:
                del tag.attrs[attr]
                continue

            if attr_lower in ("href", "src"):
                val_str = str(value).strip().lower()
                if not any(val_str.startswith(scheme) for scheme in SAFE_URL_SCHEMES):
                    del tag.attrs[attr]
                    continue

        if tag_name == "a" and tag.get("target") == "_blank":
            tag["rel"] = "noopener noreferrer"

    return str(soup)
