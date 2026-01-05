from fastapi import FastAPI, HTTPException
from typing import List
from database import init_db, add_note, get_notes, get_notes_bulk, Note
from client import fetch_locations

app = FastAPI(title="Rick & Morty AI Explorer")

# Initialize Database on Startup
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
async def read_root():
    return {"message": "Rick & Morty AI Backend is running!", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/locations")
async def get_locations(page: int = 1):
    locations = await fetch_locations(page)
    return locations

@app.post("/notes")
async def create_note(note: Note):
    return add_note(note)

@app.get("/notes/{character_id}")
async def read_notes(character_id: str):
    return get_notes(character_id)

@app.post("/notes/bulk")
async def read_notes_bulk(character_ids: List[str]):
    return get_notes_bulk(character_ids)
