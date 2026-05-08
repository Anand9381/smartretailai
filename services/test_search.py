import os
import sys

from dotenv import load_dotenv

load_dotenv()

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
except Exception:  # pragma: no cover - external SDK not installed in CI
    print("Azure SDK not installed. Install azure-search-documents and azure-core to run this SDK script.")
    sys.exit(0)

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX")
API_KEY = os.getenv("AZURE_SEARCH_KEY")

if not all([SEARCH_ENDPOINT, INDEX_NAME, API_KEY]):
    raise RuntimeError("Set AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, and AZURE_SEARCH_KEY in .env")

client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(API_KEY)
)

results = client.search("return policy")

def safe_print(value):
    print(str(value).encode("cp1252", errors="replace").decode("cp1252"))

for result in results:
    print("\n====================")
    safe_print(result)
    print("====================\n")
