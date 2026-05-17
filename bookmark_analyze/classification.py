from __future__ import annotations

from collections.abc import Mapping, Sequence

from bookmark_analyze.models import Bookmark, Classification


CATEGORY_RULES: dict[str, list[str]] = {
    "shopping": [
        "amazon",
        "rakuten",
        "uniqlo",
        "zozo",
    ],
    "ai": [
        "openai",
        "anthropic",
        "github",
        "huggingface",
    ],
    "anime": [
        "b-ch",
        "anilist",
        "myanimelist",
    ],
    "video": [
        "youtube",
        "nicovideo",
    ],
    "pharmacy": [
        "mhlw",
        "pmda",
        "yakugaku",
    ],
}

DEFAULT_TAGS: dict[str, tuple[str, ...]] = {
    "shopping": ("shopping", "ecommerce"),
    "ai": ("ai",),
    "anime": ("anime",),
    "video": ("video", "streaming"),
    "pharmacy": ("pharmacy",),
    "archive": ("archive",),
    "misc": ("misc",),
}


def classify_bookmark(
    bookmark: Bookmark,
    rules: Mapping[str, Sequence[str]] | None = None,
) -> Classification:
    rules = rules or CATEGORY_RULES
    searchable = " ".join(
        [
            bookmark.title,
            bookmark.url,
            bookmark.normalized_url,
            bookmark.folder,
            bookmark.domain,
        ]
    ).lower()

    for category, keywords in rules.items():
        if any(keyword.lower() in searchable for keyword in keywords):
            return Classification(category=category, tags=DEFAULT_TAGS.get(category, (category,)))

    if "archive" in bookmark.folder.lower():
        return Classification(category="archive", tags=DEFAULT_TAGS["archive"])

    return Classification(category="misc", tags=DEFAULT_TAGS["misc"])


def category_folder_name(category: str) -> str:
    if category.lower() == "ai":
        return "AI"
    return category.replace("_", " ").title().replace(" ", "")

