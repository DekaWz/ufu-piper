import json
import pickle
import re

import numpy as np
import faiss
import requests
import bm25s


VLLM_URL = "http://vllm-embedding:8000/v1/embeddings"
VLLM_MODEL = "Qwen/Qwen3-Embedding-4B"

INDEX_PATH = "pied-piper-index.faiss"
META_PATH = "chunks_meta.pkl"
BM25_DIR = "bm25_index"


def tokenize(text):
    """Простая токенизация: нижний регистр, только буквы и цифры."""
    return re.findall(r'[а-яёa-z0-9]+', text.lower())


def is_garbage(text):
    """Чанк — мусор, если букв меньше 30% от длины."""
    letters = len(re.findall(r'[а-яёА-ЯЁa-zA-Z]', text))
    return len(text) > 0 and (letters / len(text)) < 0.3


def build_bm25(chunks_path="chunks.jsonl"):
    with open(chunks_path, encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f if line.strip()]

    # БЕЗ фильтра — все чанки, чтобы индексы совпадали
    corpus = [tokenize(c.get("source", "") + " " + c["text"]) for c in chunks]
    retriever = bm25s.BM25()
    retriever.index(corpus)
    retriever.save(BM25_DIR)
    print(f"BM25-индекс сохранён: {BM25_DIR} ({len(corpus)} чанков)")


def load_bm25():
    return bm25s.BM25.load(BM25_DIR)


def load_index_and_chunks():
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def embed_query(query):
    r = requests.post(
        VLLM_URL,
        json={"model": VLLM_MODEL, "input": [query]},
        timeout=30,
    )
    r.raise_for_status()
    vec = np.array([r.json()["data"][0]["embedding"]], dtype=np.float32)
    faiss.normalize_L2(vec)
    return vec


def rrf_fusion(rankings, k=60):
    """Reciprocal Rank Fusion: объединяет несколько ранжированных списков."""
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


def hybrid_search(query, top_k=5, candidates=50, one_per_source=True):
    index, chunks = load_index_and_chunks()
    bm25 = load_bm25()

    # 1. Векторный поиск
    q_vec = embed_query(query)
    _, vec_ids = index.search(q_vec, candidates)
    vec_ids = [i for i in vec_ids[0].tolist() if i != -1]

    # 2. BM25 поиск
    tokens = [tokenize(query)]
    bm25_results, bm25_scores = bm25.retrieve(tokens, k=candidates)
    bm25_ids = bm25_results[0].tolist()
    bm25_scores_map = dict(zip(bm25_ids, bm25_scores[0].tolist()))

    # 3. RRF fusion
    fused = rrf_fusion([vec_ids, bm25_ids])

    seen_sources = set()
    results = []
    for doc_id, rrf_score in fused:
        if doc_id < 0 or doc_id >= len(chunks):
            continue
        chunk = chunks[doc_id]
        if is_garbage(chunk["text"]):
            continue

        source = chunk.get("source")
        if one_per_source:
            # один чанк на файл; None/пустой source не блокируем, чтобы не потерять данные
            if source and source in seen_sources:
                continue
            if source:
                seen_sources.add(source)

        results.append({
            "score": float(rrf_score),                # ключ, который ждёт app.py
            "rrf_score": float(rrf_score),
            "bm25_score": float(bm25_scores_map.get(doc_id, 0.0)),
            "text": chunk["text"],
            "source": source,
            "chunk_index": chunk.get("chunk_index"),
        })
        if len(results) >= top_k:
            break
    return results

if __name__ == "__main__":
    import sys

    # Если запускаешь впервые — сначала раскомментируй:
    #build_bm25()

    query = " ".join(sys.argv[1:]) or "эффект холла"
    for r in hybrid_search(query):
        print(f"\n[RRF={r['rrf_score']:.4f} | BM25={r['bm25_score']:.2f}]")
        print(f"{r['source']} #{r['chunk_index']}")
        print(r["text"][:300])