#!/usr/bin/env python3
"""
build_codex_refs.py

Scans all book page HTML files for [[codex:ID|Label]] shortcodes
and builds Codex/references.json with “appears in” data.

Run this AFTER you’ve built the book pages:

    python build_codex_refs.py
"""

from pathlib import Path
import re
import json


ROOT = Path(__file__).resolve().parent
BOOKS_DIR = ROOT / "Books"
OUTPUT_DIR = ROOT / "Codex"
OUTPUT_PATH = OUTPUT_DIR / "references.json"

# [[codex:some-id|Visible Text]]
CODEX_PATTERN = re.compile(r"\[\[codex:([^\|\]]+)\|([^\]]+)\]\]")

def parse_page_number(path: Path) -> int | None:
    """
    Try to extract a page number from a filename like:
    page-1.html, page1.html, 1.html, etc.
    """
    m = re.search(r"(\d+)", path.stem)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def main() -> None:
    if not BOOKS_DIR.exists():
        print(f"[ERROR] Books directory not found: {BOOKS_DIR}")
        return

    refs: dict[str, list[dict]] = {}

    # Walk Books/<bookFolder>/pages/*.html
    for book_dir in BOOKS_DIR.iterdir():
        if not book_dir.is_dir():
            continue

        meta_path = book_dir / "meta.json"
        if not meta_path.exists():
            # skip folders without meta.json
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] Failed to read {meta_path}: {e}")
            continue

        book_id = meta.get("id") or book_dir.name
        book_title = meta.get("title") or book_id

        pages_dir = book_dir / "pages"
        if not pages_dir.exists():
            print(f"[INFO] No pages/ directory for book {book_id}, skipping.")
            continue

        for page_file in sorted(pages_dir.glob("*.html")):
            page_num = parse_page_number(page_file)
            if page_num is None:
                continue

            try:
                text = page_file.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                print(f"[WARN] Failed to read {page_file}: {e}")
                continue

            for match in CODEX_PATTERN.finditer(text):
                codex_id = match.group(1).strip()
                if not codex_id:
                    continue

                refs.setdefault(codex_id, []).append({
                    "bookId": book_id,
                    "bookTitle": book_title,
                    "page": page_num
                })

    # Sort & dedupe references for each codex id
    for cid, lst in refs.items():
        lst.sort(key=lambda r: (r["bookTitle"].lower(), r["page"]))
        seen: set[tuple[str, int]] = set()
        deduped: list[dict] = []
        for r in lst:
            key = (r["bookId"], r["page"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        refs[cid] = deduped

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(refs, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"[OK] Wrote {OUTPUT_PATH} with {len(refs)} codex ids.")


if __name__ == "__main__":
    main()
