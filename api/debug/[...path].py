from fastapi import FastAPI

app = FastAPI()

@app.get("/api/debug/ping")
def ping():
    return {"status": "ok", "message": "Python function works!"}

@app.get("/api/debug/{path:path}")
def catch_all(path: str):
    return {"status": "ok", "path": path}
