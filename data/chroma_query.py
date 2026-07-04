"""
Query a local Chroma DB collection and normalize results into a
content structure the renderers can consume.

Expected metadata convention (adjust to match your actual ingestion):
  - "title": short heading for the chunk
  - "image_path": optional local path or URL to an associated image
  - "source": optional citation/source string
"""
from engine.content import ContentItem


def query_chroma(
    query: str,
    collection_name: str,
    persist_dir: str = "./chroma_data",
    n_results: int = 8,
) -> list[ContentItem]:
    import chromadb  # lazy import: only required when actually querying

    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_collection(collection_name)

    results = collection.query(query_texts=[query], n_results=n_results)

    items: list[ContentItem] = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0] if results.get("distances") else [0] * len(docs)

    for doc, meta, dist in zip(docs, metas, dists):
        meta = meta or {}
        items.append(
            ContentItem(
                text=doc,
                title=meta.get("title"),
                image_path=meta.get("image_path"),
                source=meta.get("source"),
                score=1 - dist if dist is not None else 0.0,
            )
        )
    return items
