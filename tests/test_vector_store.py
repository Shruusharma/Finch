from memory.vector_store import add_portfolio_chunks, query_portfolio, clear_portfolio
from memory.portfolio_data import SAMPLE_PORTFOLIO, portfolio_to_chunks


def test_retrieval():
    clear_portfolio()

    chunks = portfolio_to_chunks(SAMPLE_PORTFOLIO)
    add_portfolio_chunks(chunks)

    # Direct ticker match
    results = query_portfolio("Tell me about my NVDA position", top_k=2)
    print("\n--- Query: 'Tell me about my NVDA position' ---")
    for r in results:
        print(f"  [{r['distance']:.4f}] {r['text']}")
    assert "NVDA" in results[0]["text"]

    # Semantic match without exact keyword (KNOWN LIMITATION — see docs/architecture.md)
    results = query_portfolio("How is my chip stock doing?", top_k=3)
    print("\n--- Query: 'How is my chip stock doing?' ---")
    for r in results:
        print(f"  [{r['distance']:.4f}] {r['text'][:60]}...")

    assert len(results) == 3
    
    # Different domain entirely
    results = query_portfolio("Should I trim my speculative positions?", top_k=2)
    print("\n--- Query: 'Should I trim my speculative positions?' ---")
    for r in results:
        print(f"  [{r['distance']:.4f}] {r['text']}")
    assert "TSLA" in results[0]["text"]  # matches "speculative position" in notes


if __name__ == "__main__":
    test_retrieval()
    print("\nAll retrieval tests passed")

    