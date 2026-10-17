from typing import Any, List, Optional
import hashlib

from model import Chunk

from pathlib import Path

PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

PDF_OUT_PATH = PROCESSED_PATH / "pdf"
DJVU_OUT_PATH = PROCESSED_PATH / "djvu"

def get_files(files_paths: list) -> list:
    l = []
    for path in files_paths:
        l.extend([str(p) for p in path.rglob("*") if p.is_file()])

    return l

    
def get_chunks(file_path: str) -> list:
    l = 1800      # размер чанка
    s = 200       # перекрытие
    step = l - s

    chunks = []
    source = Path(file_path).stem

    with open(file_path, "r") as f:
        chunk_text = f.read(l)
        c = 0
        i = 0

        while chunk_text:
            h = hashlib.sha256(chunk_text.encode()).hexdigest()
            chunks.append(Chunk(
                identifier=f"{source}_{i}",
                text=chunk_text,
                source=source,
                chunk_index=i,
                char_start=c,
                char_end=c + len(chunk_text),
                hash_of_chunk=h,
            ))

            new_data = f.read(step)
            if not new_data:
                break

            chunk_text = chunk_text[step:] + new_data
            c += step
            i += 1

    return chunks


def write_all_chunks(c_max: int = -1) -> tuple:
    c = 0
    total_files_procced = 0
    with open("chunks.jsonl", "w", encoding="utf-8") as jsonl:
        for f in get_files([DJVU_OUT_PATH, PDF_OUT_PATH]):
            for chunk in get_chunks(f):
                jsonl.write(f"{chunk.model_dump_json()}\n")

                c += 1
            if c == c_max: break
            total_files_procced+=1
    
    return c, total_files_procced

if __name__ == "__main__":
    #print(len(get_files([PATH_STATIC_DJVU, PATH_STATIC_PDF])))

    #print(get_chunks(get_files([PATH_STATIC_DJVU, PATH_STATIC_PDF])[232]))
    a, b = write_all_chunks()
    print(f"ЗАПИСАНо ЧАНКОВввв: {a}, тотал файлов: {b}")