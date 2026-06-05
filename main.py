import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

app = FastAPI(title="朗言 AI")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/reports", StaticFiles(directory=BASE_DIR / "reports"), name="reports")


@app.get("/")
@app.head("/")
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "朗言 AI"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
