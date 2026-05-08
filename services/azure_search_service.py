from __future__ import annotations

import json
from pathlib import Path
from urllib import error, parse, request

from dotenv import load_dotenv
import os

load_dotenv()


class AzureSearchService:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[1]
        default_documents_dir = Path(__file__).resolve().parents[1] / "documents"
        self.documents_dir = Path(os.getenv("DOCUMENTS_PATH") or default_documents_dir)

    def is_configured(self) -> bool:
        return bool(os.getenv("AZURE_SEARCH_ENDPOINT") and os.getenv("AZURE_SEARCH_KEY") and os.getenv("AZURE_SEARCH_INDEX"))

    def search_documents(self, query: str, top: int = 3) -> list[dict]:
        if self.is_configured():
            remote_results = self._search_azure(query, top=top)
            if remote_results:
                return remote_results
        return self._search_local_documents(query, top=top)

    def build_context(self, query: str, top: int = 3) -> list[str]:
        return [item["content"] for item in self.search_documents(query, top=top)]

    def _search_azure(self, query: str, top: int = 3) -> list[dict]:
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT").rstrip("/")
        api_url = (
            f"{endpoint}/indexes/{os.getenv('AZURE_SEARCH_INDEX')}/docs"
            f"?api-version=2023-11-01&search={parse.quote(query)}&$top={top}"
        )
        req = request.Request(
            api_url,
            headers={"api-key": os.getenv("AZURE_SEARCH_KEY"), "Content-Type": "application/json"},
            method="GET",
        )
        try:
            with request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            values = payload.get("value", [])
            results = []
            for item in values:
                results.append(
                    {
                        "source": item.get("title") or item.get("file_name") or "azure-search-document",
                        "content": item.get("content") or item.get("chunk") or "",
                    }
                )
            return [item for item in results if item["content"]]
        except (error.URLError, json.JSONDecodeError):
            return []

    def _search_local_documents(self, query: str, top: int = 3) -> list[dict]:
        search_dirs = [self.documents_dir, self.project_root / "data"]
        keywords = [token.lower() for token in query.split() if token.strip()]
        scored = []
        for folder in search_dirs:
            if not folder.exists():
                continue
            for path in sorted(folder.iterdir()):
                if path.suffix.lower() not in {".txt", ".md", ".json", ".csv"}:
                    continue
                try:
                    content = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                if path.suffix.lower() == ".json":
                    content = self._json_to_lines(content)
                haystack = content.lower()
                score = sum(haystack.count(keyword) for keyword in keywords) or 0
                if score > 0:
                    scored.append({"source": path.name, "content": content[:2200], "score": score})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return [{"source": item["source"], "content": item["content"]} for item in scored[:top]]

    def _json_to_lines(self, content: str) -> str:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return content

        rows = payload if isinstance(payload, list) else [payload]
        lines = []
        for row in rows:
            if not isinstance(row, dict):
                lines.append(str(row))
                continue
            parts = []
            for key in (
                "name",
                "category",
                "price",
                "stock",
                "stockStatus",
                "activeOffer",
                "badge",
                "desc",
                "salesTrend",
                "salesGrowth",
                "futurePrediction",
                "stockPrediction",
            ):
                if key in row and row[key] not in (None, ""):
                    parts.append(f"{key}: {row[key]}")
            if parts:
                lines.append(" | ".join(parts))
        return "\n".join(lines) or content


azure_search_service = AzureSearchService()
