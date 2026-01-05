from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict
from database import init_db, add_note, get_notes, get_notes_bulk, Note
from client import fetch_locations, fetch_characters_by_ids, fetch_locations_by_ids
from ai_service import generate_location_summary_stream, evaluate_summary, search_knowledge_base, get_vector_store
from pydantic import BaseModel

app = FastAPI(title="Rick & Morty AI Explorer")

class SummaryRequest(BaseModel):
    name: str
    type: str
    residents: List[Dict]

class SearchRequest(BaseModel):
    query: str

# Initialize Database and Vector Store on Startup
@app.on_event("startup")
def on_startup():
    init_db()
    # Pre-load the vector store to avoid first-request timeout
    get_vector_store()

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

@app.post("/generate-summary")
async def get_summary(request: SummaryRequest):
    try:
        return StreamingResponse(
            generate_location_summary_stream(request.name, request.type, request.residents),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_endpoint(request: SearchRequest):
    try:
        print(f"🔎 Searching for: {request.query}")
        # 1. Get semantic search results
        raw_results = await search_knowledge_base(request.query)
        print(f"✅ Found {len(raw_results)} raw matches from vector store.")
        
        # 2. Extract IDs
        char_ids = []
        loc_ids = []
        
        for res in raw_results:
            meta = res["metadata"]
            print(f"   - Match: {meta.get('name')} ({meta.get('type')}) ID: {meta.get('id')}")
            if meta["type"] == "character":
                char_ids.append(meta["id"])
            elif meta["type"] == "location":
                loc_ids.append(meta["id"])
        
        # 3. Fetch full details from GraphQL
        characters = await fetch_characters_by_ids(char_ids)
        locations = await fetch_locations_by_ids(loc_ids)
        print(f"📦 Fetched {len(characters)} characters and {len(locations)} locations from GraphQL.")
        
        return {
            "characters": characters,
            "locations": locations,
            "raw_matches": raw_results # Optional: keep for debugging or relevance scores
        }
    except Exception as e:
        print(f"❌ Search Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
