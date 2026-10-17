from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from search_core import search, load_index

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR.parent / "templates"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # прогреваем индекс на старте, чтобы первый запрос не тормозил
    try:
        load_index()
        print("[startup] index loaded")
    except Exception as e:
        print(f"[startup] failed to load index: {e}")
    yield


app = FastAPI(title="Pied Piper Search", lifespan=lifespan)


class SearchResult(BaseModel):
    score: float
    text: str
    source: str | None = None
    chunk_index: int | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


@app.get("/", response_class=HTMLResponse)
async def index():
    return (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/search", response_model=SearchResponse)
async def api_search(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    top_k: int = Query(5, ge=1, le=50),
):
    try:
        results = search(q, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"query": q, "results": results}


@app.exception_handler(Exception)
async def unhandled(request, exc):
    return JSONResponse(status_code=500, content={"error": str(exc)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=True)