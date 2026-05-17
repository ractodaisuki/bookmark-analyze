from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

from bs4 import BeautifulSoup

from bookmark_analyze.models import Bookmark


def parse_firefox_bookmarks(path: Path) -> list[Bookmark]:
    html = path.read_text(encoding="utf-8")
    parser = FirefoxBookmarksParser()
    parser.feed(html)
    parser.close()

    if parser.bookmarks:
        return parser.bookmarks

    # Keep a BeautifulSoup fallback for unusually well-formed exports. Firefox's
    # native export uses loose Netscape HTML, so the event parser above is the
    # primary path.
    soup = BeautifulSoup(html, "html.parser")
    return [
        Bookmark(
            title=link.get_text(" ", strip=True),
            url=link.get("href", ""),
            add_date=link.get("add_date"),
            last_modified=link.get("last_modified"),
        )
        for link in soup.find_all("a")
    ]


class FirefoxBookmarksParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.bookmarks: list[Bookmark] = []
        self._folder_stack: list[str] = []
        self._pending_folder: str | None = None
        self._dl_folder_depth: list[bool] = []
        self._capture: str | None = None
        self._text_parts: list[str] = []
        self._link_attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_dict = {key.lower(): value or "" for key, value in attrs}

        if tag == "h3":
            self._capture = "h3"
            self._text_parts = []
            return

        if tag == "a":
            self._capture = "a"
            self._text_parts = []
            self._link_attrs = attrs_dict
            return

        if tag == "dl":
            if self._pending_folder is not None:
                self._folder_stack.append(self._pending_folder)
                self._pending_folder = None
                self._dl_folder_depth.append(True)
            else:
                self._dl_folder_depth.append(False)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag == "h3" and self._capture == "h3":
            folder = " ".join("".join(self._text_parts).split())
            if folder:
                self._pending_folder = folder
            self._reset_capture()
            return

        if tag == "a" and self._capture == "a":
            title = " ".join("".join(self._text_parts).split())
            current_path = tuple(self._folder_stack)
            self.bookmarks.append(
                Bookmark(
                    title=title,
                    url=self._link_attrs.get("href", ""),
                    folder=current_path[-1] if current_path else "",
                    folder_path=current_path,
                    add_date=self._link_attrs.get("add_date"),
                    last_modified=self._link_attrs.get("last_modified"),
                )
            )
            self._link_attrs = {}
            self._reset_capture()
            return

        if tag == "dl" and self._dl_folder_depth:
            entered_folder = self._dl_folder_depth.pop()
            if entered_folder and self._folder_stack:
                self._folder_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture in {"h3", "a"}:
            self._text_parts.append(data)

    def _reset_capture(self) -> None:
        self._capture = None
        self._text_parts = []

