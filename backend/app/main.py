from fastapi import FastAPI

app = FastAPI(title="ZT-IP Dashboard API")

@app.get("/health")
def health():
    return {"status": "ok"}