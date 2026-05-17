from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Bookmark:
    title: str
    url: str
    folder: str = ""
    folder_path: tuple[str, ...] = ()
    add_date: str | None = None
    last_modified: str | None = None
    normalized_title: str = ""
    normalized_url: str = ""
    domain: str = ""
    category: str = "misc"
    tags: list[str] = field(default_factory=list)
    duplicate: bool = False


@dataclass(frozen=True, slots=True)
class Classification:
    category: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConversionReport:
    input_path: str
    output_dir: str
    parsed: int
    written: int
    duplicates: int
    categories: dict[str, int]

