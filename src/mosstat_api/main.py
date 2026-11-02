from fastapi import FastAPI

from mosstat_api.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
