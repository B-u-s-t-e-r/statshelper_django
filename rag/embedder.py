import numpy as np
import pickle
from pathlib import Path

_model = None
MODEL_NAME = "BAAI/bge-small-en-v1.5"
CACHE_PATH = Path(__file__).parent.parent / "data" / "embeddings_cache.pkl"


def get_model():
    global _model
    if _model is None:
        try:
            from fastembed import TextEmbedding
            print(f"Loading model: {MODEL_NAME} ...")
            _model = TextEmbedding(MODEL_NAME)
            print("✅ Model loaded.")
        except ImportError:
            raise ImportError("Run: pip install fastembed==0.3.6")
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    return np.array(list(model.embed(texts)))


def embed_query(query: str) -> np.ndarray:
    model = get_model()
    return np.array(list(model.embed([query]))[0])


def save_embeddings(embeddings: np.ndarray, chunks: list[dict]):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "wb") as f:
        pickle.dump({"embeddings": embeddings, "chunks": chunks}, f)
    print(f"Embeddings cached → {CACHE_PATH}")


def load_cached_embeddings():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "rb") as f:
            data = pickle.load(f)
        print(f"Loaded {len(data['chunks'])} cached embeddings.")
        return data["embeddings"], data["chunks"]
    return None, None