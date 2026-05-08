from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.azure_search_service import azure_search_service


def safe_print(value: str) -> None:
    print(str(value).encode("cp1252", errors="replace").decode("cp1252"))


def main() -> None:
    query = "What is the return policy?"
    results = azure_search_service.search_documents(query, top=3)
    print(f"Search query: {query}")
    print(f"Results found: {len(results)}")
    for item in results:
        print("-" * 60)
        print(f"Source: {item['source']}")
        safe_print(item["content"][:600])


if __name__ == "__main__":
    main()
