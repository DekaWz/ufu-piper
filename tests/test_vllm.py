import numpy as np
import requests


VLLM_URL = "http://localhost:8000/v1/embeddings"
VLLM_MODEL = "Qwen/Qwen3-Embedding-4B"


def embed(texts):
    r = requests.post(VLLM_URL, json={"model": VLLM_MODEL, "input": texts})
    r.raise_for_status()
    return np.array([d["embedding"] for d in r.json()["data"]])


def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


query = "Что такое среднее геометрическое?"
docs = [
    "Среднее геометрическое — это корень n-й степени из произведения n чисел.",
    "Среднее арифметическое — это сумма чисел, делённая на их количество.",
    "Интеграл — это обобщение суммы для непрерывных функций.",
]

embs = embed([query] + docs)
q = embs[0]
print(f"{'Документ':<70} {'Сходство':>10}")
print("-" * 82)
for doc, vec in zip(docs, embs[1:]):
    print(f"{doc[:68]:<70} {cosine(q, vec):>10.4f}")