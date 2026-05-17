from __future__ import annotations

import json
import os
from typing import Protocol

from bookmark_analyze.models import Bookmark, Classification


CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["category", "tags"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "Classify a browser bookmark for a personal Obsidian knowledge archive. "
    "Return a compact JSON object with a lowercase category and lowercase tags. "
    "Prefer these categories when suitable: shopping, ai, anime, video, pharmacy, "
    "archive, misc."
)


class AIClassifier(Protocol):
    def classify(self, bookmark: Bookmark) -> Classification | None:
        """Return an AI classification, or None when no confident result exists."""


def build_ai_classifier(provider: str | None, model: str | None = None) -> AIClassifier | None:
    if provider is None:
        return None

    normalized = provider.lower()
    if normalized == "openai":
        return OpenAIClassifier(model=model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    if normalized == "gemini":
        return GeminiClassifier(model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    raise ValueError(f"Unsupported AI provider: {provider}")


class OpenAIClassifier:
    def __init__(self, model: str) -> None:
        self.model = model

    def classify(self, bookmark: Bookmark) -> Classification | None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError("Install bookmark-analyze[ai] to use OpenAI classification.") from exc

        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(_payload(bookmark), ensure_ascii=False)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "bookmark_classification",
                    "schema": CLASSIFICATION_SCHEMA,
                    "strict": True,
                }
            },
        )
        return _parse_classification(response.output_text)


class GeminiClassifier:
    def __init__(self, model: str) -> None:
        self.model = model

    def classify(self, bookmark: Bookmark) -> Classification | None:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError("Install bookmark-analyze[ai] to use Gemini classification.") from exc

        client = genai.Client()
        response = client.models.generate_content(
            model=self.model,
            contents=f"{SYSTEM_PROMPT}\n\n{json.dumps(_payload(bookmark), ensure_ascii=False)}",
            config={
                "response_mime_type": "application/json",
                "response_json_schema": CLASSIFICATION_SCHEMA,
            },
        )
        return _parse_classification(response.text)


def _payload(bookmark: Bookmark) -> dict[str, str]:
    return {
        "title": bookmark.title,
        "url": bookmark.normalized_url or bookmark.url,
        "folder": bookmark.folder,
    }


def _parse_classification(raw: str) -> Classification | None:
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None

    category = str(data.get("category", "")).strip().lower()
    tags = [
        str(tag).strip().lower()
        for tag in data.get("tags", [])
        if str(tag).strip()
    ]
    if not category:
        return None
    return Classification(category=category, tags=tuple(dict.fromkeys(tags or [category])))

