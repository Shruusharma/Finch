import logging
import chromadb


logger = logging.getLogger(__name__)

# Persistent client — data survives restarts, stored in ./chroma_data
client = chromadb.PersistentClient(path="./chroma_data")

COLLECTION_NAME = "portfolio"

collection = client.get_or_create_collection(name=COLLECTION_NAME)


def add_portfolio_chunks(chunks: list[dict]) -> None:
    """
    Adds portfolio chunks to the vector store.

    Args:
        chunks: list of dicts, each with:
            - id: unique string id
            - text: the chunk's text content (what gets embedded)
            - metadata: dict of extra structured data (ticker, shares, etc.)
    """
    logger.info(f"Adding {len(chunks)} portfolio chunks to vector store")

    collection.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )


def query_portfolio(query_text: str, top_k: int = 3) -> list[dict]:
    """
    Retrieves the top-k most relevant portfolio chunks for a query.

    Args:
        query_text: the user's natural-language question
        top_k: number of chunks to retrieve

    Returns:
        list of dicts with 'text', 'metadata', and 'distance' (lower = more similar)
    """
    logger.info(f"Querying portfolio for: '{query_text}' (top_k={top_k})")

    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return chunks


def clear_portfolio() -> None:
    """Deletes all chunks in the portfolio collection. Useful for testing."""
    global collection
    client.delete_collection(name=COLLECTION_NAME)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    logger.info("Portfolio collection cleared")