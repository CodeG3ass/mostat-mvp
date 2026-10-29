from fastapi import FastAPI


app = FastAPI(
    title="Mosstat API",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
