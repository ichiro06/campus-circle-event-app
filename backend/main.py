from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Campus Circle API is ready"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/circles")
def list_circles():
    return [
        {"name": "プログラミング研究会", "category": "技術"},
        {"name": "軽音サークル", "category": "音楽"},
        {"name": "フットサル同好会", "category": "スポーツ"},
    ]
