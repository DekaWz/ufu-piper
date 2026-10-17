import json
import pickle
from pathlib import Path

import numpy as np
import faiss
import requests
from tqdm import tqdm


VLLM_URL = "http://localhost:8000/v1/embeddings"
VLLM_MODEL = "Qwen/Qwen3-Embedding-4B"

BATCH_SIZE = 8
CHUNKS_PATH = "chunks.jsonl"
INDEX_PATH = "pied-piper-index.faiss"
META_PATH = "chunks_meta.pkl"
EMBEDDINGS_PATH = "embeddings.npy"


def load_chunks(path):
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return [c for c in chunks if c.get("text", "").strip()]


def embed_texts(texts, batch_size=BATCH_SIZE):
    all_embeddings = []

    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch = texts[i:i + batch_size]
        response = requests.post(
            VLLM_URL,
            json={"model": VLLM_MODEL, "input": batch},
            timeout=120,
        )
        response.raise_for_status()
        batch_emb = [item["embedding"] for item in response.json()["data"]]
        all_embeddings.extend(batch_emb)

    embeddings = np.array(all_embeddings, dtype=np.float32)
    print(f"Форма эмбеддингов: {embeddings.shape}")
    return embeddings


def build_and_save_index(embeddings, chunks):
    embeddings_norm = embeddings.copy()
    faiss.normalize_L2(embeddings_norm)

    dim = embeddings_norm.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings_norm)
    print(f"В индексе: {index.ntotal} векторов, dim={dim}")

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(chunks, f)
    np.save(EMBEDDINGS_PATH, embeddings_norm)

    print(f"Сохранено: {INDEX_PATH}, {META_PATH}, {EMBEDDINGS_PATH}")


def main():
    chunks = load_chunks(CHUNKS_PATH)
    texts = [c["text"] for c in chunks]
    print(f"Чанков: {len(texts)}")

    embeddings = embed_texts(texts)
    build_and_save_index(embeddings, chunks)


if __name__ == "__main__":
    main()