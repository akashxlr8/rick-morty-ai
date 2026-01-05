import sqlite3
from pydantic import BaseModel
from typing import List, Optional
import time

DB_NAME = "notes.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

class Note(BaseModel):
    character_id: str
    content: str
    timestamp: Optional[float] = None

def add_note(note: Note):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = time.time()
    c.execute("INSERT INTO notes (character_id, content, timestamp) VALUES (?, ?, ?)",
              (note.character_id, note.content, timestamp))
    conn.commit()
    conn.close()
    return {**note.dict(), "timestamp": timestamp}

def get_notes(character_id: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT content, timestamp FROM notes WHERE character_id = ? ORDER BY timestamp DESC", (character_id,))
    rows = c.fetchall()
    conn.close()
    return [{"content": r[0], "timestamp": r[1]} for r in rows]

def get_notes_bulk(character_ids: List[str]):
    if not character_ids:
        return {}
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    placeholders = ','.join('?' for _ in character_ids)
    query = f"SELECT character_id, content, timestamp FROM notes WHERE character_id IN ({placeholders}) ORDER BY timestamp DESC"
    c.execute(query, character_ids)
    rows = c.fetchall()
    conn.close()
    
    # Group by character_id
    notes_map = {cid: [] for cid in character_ids}
    for r in rows:
        cid, content, ts = r
        if cid in notes_map:
            notes_map[cid].append({"content": content, "timestamp": ts})
    return notes_map
