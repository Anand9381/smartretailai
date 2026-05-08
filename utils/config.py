from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv


dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    load_dotenv()


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass(frozen=True)
class AppConfig:
    groq_api_key: str = env("GROQ_API_KEY")
    groq_model: str = env("GROQ_MODEL", "groq/meta-llama/llama-4-scout-17b-16e-instruct")
    azure_search_endpoint: str = env("AZURE_SEARCH_ENDPOINT")
    azure_search_key: str = env("AZURE_SEARCH_KEY")
    azure_search_index: str = env("AZURE_SEARCH_INDEX", "smart-documents-index")
    embedding_model: str = env("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    faiss_store_path: str = env("FAISS_STORE_PATH", "vector_store/faiss_index")
    documents_path: str = env("DOCUMENTS_PATH", "documents")


config = AppConfig()
