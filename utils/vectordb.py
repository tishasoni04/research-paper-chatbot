import chromadb
from chromadb.config import Settings


def get_chroma_collection(collection_name: str = "papers", persist_dir: str = "data/chroma_db"):
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )

    print("Chroma persist path:", persist_dir)

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


