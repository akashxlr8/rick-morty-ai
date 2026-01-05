from pydantic import BaseModel
from typing import List, Optional
import time
import os
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()
# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    """
    Initialize database - creates table if it doesn't exist.
    For Supabase, create the table manually in the Supabase dashboard using:
    
    CREATE TABLE IF NOT EXISTS notes (
        id BIGSERIAL PRIMARY KEY,
        character_id TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DOUBLE PRECISION NOT NULL
    );
    CREATE INDEX idx_character_id ON notes(character_id);
    """
    pass  # Table creation should be done via Supabase dashboard

class Note(BaseModel):
    character_id: str
    content: str
    timestamp: Optional[float] = None

def add_note(note: Note):
    timestamp = time.time()
    response = supabase.table("notes").insert({
        "character_id": note.character_id,
        "content": note.content,
        "timestamp": timestamp
    }).execute()
    
    if not response.data:
        raise Exception("Failed to insert note")
    
    return {"character_id": note.character_id, "content": note.content, "timestamp": timestamp}

def get_notes(character_id: str):
    response = supabase.table("notes").select("content, timestamp").eq("character_id", character_id).order("timestamp", desc=True).execute()
    return [{"content": r["content"], "timestamp": r["timestamp"]} for r in response.data]

def get_notes_bulk(character_ids: List[str]):
    if not character_ids:
        return {}
    
    # Supabase doesn't support IN operator the same way, so we fetch all and filter
    response = supabase.table("notes").select("character_id, content, timestamp").in_("character_id", character_ids).order("timestamp", desc=True).execute()
    
    # Group by character_id
    notes_map = {cid: [] for cid in character_ids}
    for r in response.data:
        cid = r["character_id"]
        if cid in notes_map:
            notes_map[cid].append({"content": r["content"], "timestamp": r["timestamp"]})
    return notes_map
