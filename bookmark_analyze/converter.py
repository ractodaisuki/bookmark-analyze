from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

from bookmark_analyze.ai import AIClassifier
from bookmark_analyze.classification import CATEGORY_RULES, classify_bookmark
from bookmark_analyze.markdown import write_bookmark_notes
from bookmark_analyze.models import Bookmark, ConversionReport
from bookmark_analyze.normalization import extract_domain, normalize_title, normalize_url
from bookmark_analyze.parser import parse_firefox_bookmarks


def convert_bookmarks(
    input_path: Path,
    output_dir: Path,
    rules: Mapping[str, Sequence[str]] | None = None,
    ai_classifier: AIClassifier | None = None,
) -> ConversionReport:
    bookmarks = parse_firefox_bookmarks(input_path)
    enrich_bookmarks(bookmarks, rules=rules, ai_classifier=ai_classifier)
    written = write_bookmark_notes(bookmarks, output_dir)
    category_counts = Counter(bookmark.category for bookmark in bookmarks)
    duplicate_count = sum(1 for bookmark in bookmarks if bookmark.duplicate)

    return ConversionReport(
        input_path=str(input_path),
        output_dir=str(output_dir),
        parsed=len(bookmarks),
        written=written,
        duplicates=duplicate_count,
        categories=dict(sorted(category_counts.items())),
    )


def enrich_bookmarks(
    bookmarks: list[Bookmark],
    rules: Mapping[str, Sequence[str]] | None = None,
    ai_classifier: AIClassifier | None = None,
) -> None:
    rules = rules or CATEGORY_RULES

    for bookmark in bookmarks:
        bookmark.normalized_title = normalize_title(bookmark.title)
        bookmark.normalized_url = normalize_url(bookmark.url)
        bookmark.domain = extract_domain(bookmark.normalized_url)

    normalized_counts = Counter(bookmark.normalized_url for bookmark in bookmarks)
    for bookmark in bookmarks:
        bookmark.duplicate = normalized_counts[bookmark.normalized_url] > 1

        classification = classify_bookmark(bookmark, rules)
        if ai_classifier is not None:
            ai_classification = ai_classifier.classify(bookmark)
            if ai_classification is not None:
                classification = ai_classification

        bookmark.category = classification.category
        bookmark.tags = list(dict.fromkeys(classification.tags or (classification.category,)))

