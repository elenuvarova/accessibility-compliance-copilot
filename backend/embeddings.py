import json

import numpy as np

_model = None


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _model


def embed(texts: list) -> list:
    model = _get_model()
    return [v.tolist() for v in model.embed(texts)]


def cosine_sim(a: list, b: list) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(np.dot(va, vb) / denom) if denom > 0 else 0.0


def top_k_chunks(query: str, chunks: list, k: int = 3) -> list:
    if not chunks:
        return []
    q_emb = embed([query])[0]
    scored = []
    for chunk in chunks:
        try:
            c_emb = json.loads(chunk.embedding)
            scored.append((cosine_sim(q_emb, c_emb), chunk))
        except Exception:
            pass
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:k]]
