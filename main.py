from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()

@app.get("/tool-manifest.json")
def get_manifest():
    manifest_path = os.path.join(os.getcwd(), "tool-manifest.json")
    return FileResponse(manifest_path, media_type="application/json")
