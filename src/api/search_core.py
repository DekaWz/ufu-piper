import json
import pickle

import numpy as np
import faiss
import requests

VLLM_URL = "http://localhost:8000/v1/embeddings"
VLLM_MODEL = "Qwen/Qwen3-Embedding-4B"

INDEX_PATH = "pied-piper-index.faiss"
META_PATH = "chunks_meta.pkl"


def load_index():
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def embed_query(query):
    response = requests.post(
        VLLM_URL,
        json={"model": VLLM_MODEL, "input": [query]},
        timeout=30,
    )
    response.raise_for_status()
    vec = np.array([response.json()["data"][0]["embedding"]], dtype=np.float32)
    faiss.normalize_L2(vec)
    return vec


def search(query, top_k=5):
    index, chunks = load_index()
    q_vec = embed_query(query)
    scores, ids = index.search(q_vec, top_k)

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        chunk = chunks[idx]
        results.append({
            "score": float(score),
            "text": chunk["text"],
            "source": chunk.get("source"),
            "chunk_index": chunk.get("chunk_index"),
        })
    return results


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "Что такое неравенство о средних?"
    for r in search(query):
        print(f"\n[{r['score']:.4f}] {r['source']} #{r['chunk_index']}")
        print(r["text"])
        