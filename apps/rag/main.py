from fastapi import FastAPI

app = FastAPI()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/ask")
async def ask(query: str):
    # Placeholder RAG endpoint
    return {"answer": "Not implemented yet."}
