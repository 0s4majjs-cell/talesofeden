import os
import json
import html
import re

BOOKS_ROOT = "Books"
BOOKS_JSON = "books.json"

# Approximate size of a "normal" page
TARGET_CHARS_PER_PAGE = 1000   # tweak up/down if needed

# If a page immediately before a chapter heading has fewer characters than this,
# we merge it into the page before it (to avoid orphan/tiny pages).
MIN_CHARS_PER_PAGE = 450

# ===========================
# Inline formatting
# ===========================

def inline_format(text: str) -> str:
    """
    Apply simple inline formatting to a line of plain text.

    Supported:
      *text*       -> <em>text</em>
      **text**     -> <strong>text</strong>
      ***text***   -> <strong><em>text</em></strong>

    Order matters: handle *** first, then **, then *.
    All text is HTML-escaped first so this is safe.
    """
    safe = html.escape(text)

    # bold+italic ***text***
    safe = re.sub(r"\*\*\*([^*]+)\*\*\*", r"<strong><em>\1</em></strong>", safe)

    # bold **text**
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)

    # italic *text*
    safe = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", safe)

    return safe

# ===========================
# Block -> HTML
# ===========================

def block_to_html(block_text: str) -> str:
    """
    Turn a block of plain text into HTML.
    - Every non-empty line becomes its own paragraph.
    - Lines starting with '# ' become big titles.
    - Inline *italic*, **bold**, ***bold+italic*** are supported.
    """
    html_parts = []

    for line in block_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("# "):
            title_raw = stripped[2:].strip()
            title = inline_format(title_raw)
            html_parts.append(f'<h2 class="chapter-title">{title}</h2>')
        else:
            formatted = inline_format(stripped)
            html_parts.append(f"<p>{formatted}</p>")

    return "\n".join(html_parts)

# ===========================
# Split manuscript into paragraphs + forced breaks
# ===========================

def parse_paragraphs(text: str):
    """
    Turn raw manuscript text into a list of paragraphs and forced page breaks.

    Returns a list where each element is either:
      - a paragraph string
      - the special token '__PAGE_BREAK__'
    """
    paragraphs = []
    current_lines = []

    for raw_line in text.split("\n"):
        line = raw_line.rstrip("\r")

        # manual hard page break
        if line.strip() == "===PAGE===":
            if current_lines:
                paragraphs.append("\n".join(current_lines).strip())
                current_lines = []
            paragraphs.append("__PAGE_BREAK__")
            continue

        if not line.strip():
            # Blank line -> paragraph break
            if current_lines:
                paragraphs.append("\n".join(current_lines).strip())
                current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        paragraphs.append("\n".join(current_lines).strip())

    return paragraphs

# ===========================
# Build pages from paragraphs
# ===========================

def build_pages_from_paragraphs(paragraphs):
    """
    Given a list of paragraphs + '__PAGE_BREAK__' tokens,
    return a list of pages. Each page is a string of text
    (paragraphs separated by blank lines) intended to be
    rendered into one visual page.

    Rules:
    - '# ' headings always start a fresh page.
    - If the page *before* a chapter heading is very short,
      we merge that short page into the one before it.
    - After paginating, if any page consists of *only* a heading,
      we merge it with the following page so headings are never alone.
    """
    pages = []
    current = []
    current_len = 0

    for para in paragraphs:
        if para == "__PAGE_BREAK__":
            if current:
                pages.append("\n\n".join(current))
                current = []
                current_len = 0
            continue

        is_heading = para.lstrip().startswith("# ")

        if is_heading:
            # We're about to start a new chapter/section.
            # First, finalize the current page (tail of previous chapter).
            if current:
                if len(pages) > 0 and current_len < MIN_CHARS_PER_PAGE:
                    # Orphan page: merge into previous page
                    merged = "\n\n".join([pages[-1], "\n\n".join(current)])
                    pages[-1] = merged
                else:
                    pages.append("\n\n".join(current))
                current = []
                current_len = 0

            # Start new page with heading
            current.append(para)
            current_len = len(para)
            continue

        # Normal paragraph
        para_len = len(para)

        if current and (current_len + para_len > TARGET_CHARS_PER_PAGE):
            pages.append("\n\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len

    if current:
        pages.append("\n\n".join(current))

    # --- Post-process: merge any heading-only pages with the following page ---
    i = 0
    while i < len(pages) - 1:
        blocks = [b for b in pages[i].split("\n\n") if b.strip()]
        if len(blocks) == 1 and blocks[0].lstrip().startswith("# "):
            # Page i has only a single heading: merge with page i+1
            pages[i] = pages[i] + "\n\n" + pages[i + 1]
            del pages[i + 1]
            # Don't increment i so we can re-check this merged page if needed
            continue
        i += 1

    return pages

# ===========================
# Page building for a single book
# ===========================

def build_pages_for_book(book_dir: str) -> int:
    manuscript_path = os.path.join(book_dir, "manuscript.txt")
    pages_dir = os.path.join(book_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    if not os.path.exists(manuscript_path):
        print(f"  [!] No manuscript.txt in {book_dir}, skipping pages")
        return 0

    with open(manuscript_path, "r", encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")

    paragraphs = parse_paragraphs(text)
    raw_pages = build_pages_from_paragraphs(paragraphs)

    template = """<article class="page-column">
{content}
</article>
"""

    for i, raw in enumerate(raw_pages, start=1):
        content_html = block_to_html(raw)
        out_html = template.format(content=content_html)
        out_path = os.path.join(pages_dir, f"page{i}.html")
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(out_html)

    print(f"  ✓ Generated {len(raw_pages)} pages in {pages_dir}")
    return len(raw_pages)

# ===========================
# Main
# ===========================

def main():
    books_meta = []

    if not os.path.isdir(BOOKS_ROOT):
        print(f"No '{BOOKS_ROOT}' folder found.")
        return

    for name in os.listdir(BOOKS_ROOT):
        book_dir = os.path.join(BOOKS_ROOT, name)
        if not os.path.isdir(book_dir):
            continue

        print(f"Processing book: {name}")
        meta_path = os.path.join(book_dir, "meta.json")

        if not os.path.exists(meta_path):
            print(f"  [!] No meta.json in {book_dir}, skipping this book")
            continue

        with open(meta_path, "r", encoding="utf-8") as mf:
            meta = json.load(mf)

        total_pages = build_pages_for_book(book_dir)

        meta["id"] = meta.get("id", name)
        meta["path"] = f"{BOOKS_ROOT}/{name}/index.html"
        meta["totalPages"] = total_pages

        books_meta.append(meta)

    with open(BOOKS_JSON, "w", encoding="utf-8") as out:
        json.dump(books_meta, out, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(books_meta)} books to {BOOKS_JSON}")

if __name__ == "__main__":
    main()
# cd path\to\tales-of-eden
# python build_books.py
