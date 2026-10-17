from pydantic import BaseModel

class Chunk(BaseModel):
    identifier: str
    text: str
    source: str
    chunk_index: int
    char_start: int
    char_end: int
    hash_of_chunk: str