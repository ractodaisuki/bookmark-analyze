from __future__ import annotations

import yaml

from bookmark_analyze.converter import convert_bookmarks
from bookmark_analyze.normalization import extract_domain, normalize_title, normalize_url
from bookmark_analyze.parser import parse_firefox_bookmarks


SAMPLE_BOOKMARKS = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
  <DT><H3 ADD_DATE="1715817600" LAST_MODIFIED="1715817700">Shopping</H3>
  <DL><p>
    <DT><A HREF="http://www.amazon.co.jp/abc/?utm_source=x&amp;gclid=y" ADD_DATE="1715817600">Amazon / Test</A>
    <DT><A HREF="https://www.amazon.co.jp/abc" ADD_DATE="1715817600">Amazon duplicate</A>
  </DL><p>
  <DT><H3>Research</H3>
  <DL><p>
    <DT><A HREF="https://github.com/openai/openai-python/" ADD_DATE="1715904000" LAST_MODIFIED="1715990400">OpenAI SDK</A>
    <DT><A HREF="https://example.com/path/?utm_campaign=sale&amp;keep=1">Example</A>
  </DL><p>
</DL><p>
"""


def test_normalize_url_removes_tracking_and_upgrades_scheme() -> None:
    assert (
        normalize_url("http://Example.com/path/?utm_source=x&keep=1&fbclid=y")
        == "https://example.com/path?keep=1"
    )


def test_normalize_title_removes_invalid_filename_chars() -> None:
    assert normalize_title('Amazon / Test: "A"') == "Amazon Test A"


def test_extract_domain_removes_www() -> None:
    assert extract_domain("https://www.amazon.co.jp/abc") == "amazon.co.jp"


def test_parse_firefox_bookmarks(tmp_path) -> None:
    source = tmp_path / "bookmarks.html"
    source.write_text(SAMPLE_BOOKMARKS, encoding="utf-8")

    bookmarks = parse_firefox_bookmarks(source)

    assert len(bookmarks) == 4
    assert bookmarks[0].folder == "Shopping"
    assert bookmarks[2].folder_path == ("Research",)


def test_convert_bookmarks_writes_dataview_ready_notes(tmp_path) -> None:
    source = tmp_path / "bookmarks.html"
    output = tmp_path / "ObsidianVault" / "Bookmarks"
    source.write_text(SAMPLE_BOOKMARKS, encoding="utf-8")

    report = convert_bookmarks(source, output)

    assert report.parsed == 4
    assert report.written == 4
    assert report.duplicates == 2
    assert report.categories["shopping"] == 2
    assert report.categories["ai"] == 1

    shopping_notes = sorted((output / "Shopping").glob("*.md"))
    assert len(shopping_notes) == 2

    first_note = shopping_notes[0].read_text(encoding="utf-8")
    frontmatter = first_note.split("---", 2)[1]
    data = yaml.safe_load(frontmatter)
    assert data["duplicate"] is True
    assert data["domain"] == "amazon.co.jp"
    assert data["category"] == "shopping"
    assert "shopping" in data["tags"]
