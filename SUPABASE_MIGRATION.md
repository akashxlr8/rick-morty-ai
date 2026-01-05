# Supabase Migration Guide

## Step 1: Create a Supabase Project
1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Create a new project
4. Save your project URL and anon public key

## Step 2: Create the Database Table
1. Go to the SQL Editor in your Supabase project dashboard
2. Run the following SQL:

```sql
CREATE TABLE IF NOT EXISTS notes (
    id BIGSERIAL PRIMARY KEY,
    character_id TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DOUBLE PRECISION NOT NULL
);

CREATE INDEX idx_character_id ON notes(character_id);
```

## Step 3: Set Environment Variables
1. Create a `.env` file in the `backend` folder with the following:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
```

Replace with your actual Supabase credentials from the Settings > API section.

## Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 5: Migrate Data (Optional)
If you have existing data in the local SQLite database, you can migrate it:

```python
import sqlite3
from backend.database import supabase

# Read from old SQLite database
conn = sqlite3.connect("notes.db")
c = conn.cursor()
c.execute("SELECT character_id, content, timestamp FROM notes")
rows = c.fetchall()
conn.close()

# Insert into Supabase
for character_id, content, timestamp in rows:
    supabase.table("notes").insert({
        "character_id": character_id,
        "content": content,
        "timestamp": timestamp
    }).execute()

print(f"Migrated {len(rows)} notes to Supabase!")
```

## Step 6: Run Your Application
```bash
uvicorn main:app --reload
```

## Notes
- The function signatures remain the same, so no changes needed in `main.py`
- Supabase provides better scalability and reliability than SQLite
- You can manage your data directly from the Supabase dashboard
- Row-level security (RLS) can be configured for production use
