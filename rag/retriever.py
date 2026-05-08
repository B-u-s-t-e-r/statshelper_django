
import numpy as np
from pathlib import Path
import pickle

_index = None
_chunks = None

INDEX_PATH = Path(__file__).parent.parent / "data" / "faiss_index.pkl"


def build_index(embeddings: np.ndarray, chunks: list[dict]):
    """
    Build a FAISS index from embeddings.
    Uses flat L2 index (exact search — fine for small KBs).
    """
    global _index, _chunks
    try:
        import faiss
    except ImportError:
        raise ImportError("faiss-cpu not installed.\nRun: pip install faiss-cpu")

    dim = embeddings.shape[1]
    # Normalize for cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-10)

    index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity on normalized vecs
    index.add(normalized.astype(np.float32))

    _index = index
    _chunks = chunks

    # Save to disk
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"index_vectors": normalized, "chunks": chunks}, f)
    print(f"FAISS index built with {index.ntotal} vectors.")
    return index, chunks


def load_index():
    """Load FAISS index from disk."""
    global _index, _chunks
    if _index is not None:
        return _index, _chunks

    if not INDEX_PATH.exists():
        return None, None

    try:
        import faiss
    except ImportError:
        raise ImportError("faiss-cpu not installed.\nRun: pip install faiss-cpu")

    with open(INDEX_PATH, "rb") as f:
        data = pickle.load(f)

    vectors = data["index_vectors"]
    _chunks = data["chunks"]
    dim = vectors.shape[1]
    _index = faiss.IndexFlatIP(dim)
    _index.add(vectors.astype(np.float32))
    print(f"FAISS index loaded: {_index.ntotal} vectors.")
    return _index, _chunks


def retrieve(query_embedding: np.ndarray, top_k: int = 3) -> list[dict]:
    """
    Retrieve top-k most similar KB entries for a query embedding.
    Returns list of (score, metadata) dicts.
    """
    global _index, _chunks

    if _index is None:
        _index, _chunks = load_index()

    if _index is None:
        raise RuntimeError("No FAISS index found. Run build_kb.py first.")

    # Normalize query
    q = query_embedding.astype(np.float32).reshape(1, -1)
    q = q / (np.linalg.norm(q) + 1e-10)

    scores, indices = _index.search(q, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append({
                "score": float(score),
                "entry": _chunks[idx]["metadata"]
            })
    return results


def keyword_fallback(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """
    Simple keyword matching fallback when semantic search scores are low.
    No ML needed.
    """
    query_lower = query.lower()
    scored = []
    for chunk in chunks:
        entry = chunk["metadata"]
        score = 0
        # Check keywords
        for kw in entry.get("keywords", []):
            if kw.lower() in query_lower:
                score += 2
        # Check concept name
        if entry["concept"].lower() in query_lower:
            score += 3
        # Check category
        if entry["category"].lower() in query_lower:
            score += 1
        if score > 0:
            scored.append({"score": score / 10.0, "entry": entry})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    from embedder import embed_query, load_cached_embeddings
    embs, chunks = load_cached_embeddings()
    if embs is not None:
        build_index(embs, chunks)
        q_emb = embed_query("compare two group means t-test")
        results = retrieve(q_emb)
        for r in results:
            print(f"Score: {r['score']:.4f} | {r['entry']['concept']}")