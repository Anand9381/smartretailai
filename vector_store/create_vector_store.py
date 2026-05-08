from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config import config


def build_local_document_payload() -> list[dict]:
    documents_dir = Path(config.documents_path)
    payload = []
    for path in sorted(documents_dir.glob("*")):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        payload.append({"source": path.name, "content": path.read_text(encoding="utf-8")})
    return payload


def create_vector_store() -> None:
    store_dir = Path(config.faiss_store_path)
    store_dir.mkdir(parents=True, exist_ok=True)
    payload = build_local_document_payload()
    (store_dir / "documents.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved local document metadata to {store_dir / 'documents.json'}")

    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceEmbeddings
    except Exception:
        print("Optional LangChain or embedding packages are not installed yet. Saved fallback metadata only.")
        return

    texts = []
    metadatas = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)
    for item in payload:
        for chunk in splitter.split_text(item["content"]):
            texts.append(chunk)
            metadatas.append({"source": item["source"]})

    if not texts:
        print("No document chunks found.")
        return

    embeddings = HuggingFaceEmbeddings(model_name=config.embedding_model)
    vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    vector_store.save_local(str(store_dir))
    print(f"Saved FAISS vector store to {store_dir}")


if __name__ == "__main__":
    create_vector_store()
