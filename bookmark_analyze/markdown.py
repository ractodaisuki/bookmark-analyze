from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

import yaml

from bookmark_analyze.classification import category_folder_name
from bookmark_analyze.models import Bookmark
from bookmark_analyze.normalization import epoch_to_date, slugify_filename


def write_bookmark_notes(bookmarks: list[Bookmark], output_root: Path) -> int:
    output_root.mkdir(parents=True, exist_ok=True)
    used_paths: set[Path] = set()
    written = 0

    for bookmark in bookmarks:
        category_dir = output_root / category_folder_name(bookmark.category)
        category_dir.mkdir(parents=True, exist_ok=True)
        note_path = _unique_note_path(category_dir, bookmark, used_paths)
        note_path.write_text(render_markdown(bookmark), encoding="utf-8")
        used_paths.add(note_path)
        written += 1

    return written


def render_markdown(bookmark: Bookmark) -> str:
    frontmatter = {
        "title": bookmark.normalized_title or bookmark.title,
        "url": bookmark.normalized_url or bookmark.url,
        "domain": bookmark.domain,
        "folder": bookmark.folder,
        "folder_path": list(bookmark.folder_path),
        "category": bookmark.category,
        "tags": bookmark.tags,
        "created": date.fromisoformat(epoch_to_date(bookmark.add_date)),
    }
    if bookmark.last_modified:
        frontmatter["last_modified"] = date.fromisoformat(epoch_to_date(bookmark.last_modified))
    if bookmark.duplicate:
        frontmatter["duplicate"] = True

    yaml_text = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()

    title = bookmark.normalized_title or bookmark.title
    url = bookmark.normalized_url or bookmark.url
    return (
        f"---\n{yaml_text}\n---\n\n"
        f"# {title}\n\n"
        "## URL\n"
        f"{url}\n\n"
        "## Memo\n\n"
        "## Related\n"
    )


def _unique_note_path(category_dir: Path, bookmark: Bookmark, used_paths: set[Path]) -> Path:
    base_name = slugify_filename(bookmark.normalized_title or bookmark.title)
    candidate = category_dir / f"{base_name}.md"
    if candidate not in used_paths and not candidate.exists():
        return candidate

    digest = hashlib.sha1((bookmark.normalized_url or bookmark.url).encode("utf-8")).hexdigest()[:8]
    candidate = category_dir / f"{base_name} - {digest}.md"
    if candidate not in used_paths and not candidate.exists():
        return candidate

    counter = 2
    while True:
        numbered = category_dir / f"{base_name} - {digest}-{counter}.md"
        if numbered not in used_paths and not numbered.exists():
            return numbered
        counter += 1
