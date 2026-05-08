from pathlib import Path


DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"
SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_documents():
    documents = []
    for file_path in sorted(DOCUMENTS_DIR.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            content = file_path.read_text(encoding="utf-8")
            document = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "content": content,
                "content_type": file_path.suffix.lower().lstrip("."),
            }
            documents.append(document)
    return documents


def print_documents(documents):
    for document in documents:
        print("=" * 80)
        print(f"File: {document['file_name']}")
        print(f"Path: {document['file_path']}")
        print(f"Type: {document['content_type']}")
        print("-" * 80)
        print(document["content"])
        print()


def build_index_payload(documents):
    payload = []
    for index, document in enumerate(documents, start=1):
        payload.append(
            {
                "id": str(index),
                "title": document["file_name"],
                "source_path": document["file_path"],
                "content": document["content"],
                "content_type": document["content_type"],
            }
        )
    return payload


def main():
    if not DOCUMENTS_DIR.exists():
        print(f"Documents folder not found: {DOCUMENTS_DIR}")
        return

    documents = load_documents()
    if not documents:
        print("No supported documents found.")
        return

    print_documents(documents)

    index_payload = build_index_payload(documents)
    print("=" * 80)
    print("Prepared payload for future Azure AI Search indexing")
    print(f"Total documents: {len(index_payload)}")
    for item in index_payload:
        print(f"- {item['id']}: {item['title']}")


if __name__ == "__main__":
    main()
