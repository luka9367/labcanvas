#!/usr/bin/env python3
"""Test server script."""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Test Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "backend", "app", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root():
    return {"message": "Server is running"}

@app.get("/api/v1/gallery")
def get_gallery():
    import json
    gallery_path = os.path.join(static_dir, "gallery", "gallery.json")
    with open(gallery_path, encoding='utf-8') as f:
        data = json.load(f)
    return {"data": data[:5], "count": len(data)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
