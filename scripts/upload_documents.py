from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib import request
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config import config


def load_documents() -> list[dict]:
    documents_dir = Path(config.documents_path)
    docs = []
    for index, path in enumerate(sorted(documents_dir.iterdir()), start=1):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        docs.append(
            {
                "@search.action": "mergeOrUpload",
                "id": str(index),
                "title": path.name,
                "file_name": path.name,
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return docs


def upload() -> None:
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT").rstrip("/")
    url = f"{endpoint}/indexes/{os.getenv('AZURE_SEARCH_INDEX')}/docs/index?api-version=2023-11-01"
    payload = {"value": load_documents()}
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"api-key": os.getenv("AZURE_SEARCH_KEY"), "Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        print(response.read().decode("utf-8"))


if __name__ == "__main__":
    if not config.azure_search_endpoint or not config.azure_search_key:
        print("Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY in .env before uploading.")
    else:
        upload()
