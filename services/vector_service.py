from __future__ import annotations

import json
from pathlib import Path

from utils.config import config


class VectorStoreService:
    def __init__(self) -> None:
        self.store_path = Path(config.faiss_store_path)
        self.metadata_file = self.store_path / "documents.json"

    def load_metadata(self) -> list[dict]:
        if not self.metadata_file.exists():
            return []
        return json.loads(self.metadata_file.read_text(encoding="utf-8"))

    def simple_retrieve(self, query: str, top: int = 3) -> list[dict]:
        keywords = [token.lower() for token in query.split() if token.strip()]
        scored = []
        for item in self.load_metadata():
            content = item.get("content", "").lower()
            score = sum(content.count(keyword) for keyword in keywords)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in scored[:top]]


vector_service = VectorStoreService()
