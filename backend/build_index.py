import os
import asyncio
import httpx
import toml
from typing import List, Dict
from langchain_core.documents import Document
from langchain_community.embeddings import JinaEmbeddings
from langchain_community.vectorstores import FAISS

# Try to load secrets if env var is missing
try:
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "OPENAI_API_KEY" in secrets and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
            print("Loaded OPENAI_API_KEY from secrets.toml")
        if "JINA_API_KEY" in secrets and "JINA_API_KEY" not in os.environ:
            os.environ["JINA_API_KEY"] = secrets["JINA_API_KEY"]
            print("Loaded JINA_API_KEY from secrets.toml")
except Exception as e:
    print(f"Warning: Could not load secrets: {e}")

GRAPHQL_URL = "https://rickandmortyapi.com/graphql"

QUERY_CHARACTERS = """
query ($page: Int) {
  characters(page: $page) {
    info {
      next
    }
    results {
      id
      name
      status
      species
      type
      gender
      origin {
        name
      }
      location {
        name
      }
    }
  }
}
"""

QUERY_LOCATIONS = """
query ($page: Int) {
  locations(page: $page) {
    info {
      next
    }
    results {
      id
      name
      type
      dimension
      residents {
        name
      }
    }
  }
}
"""

async def fetch_all_pages(query: str, key: str):
    all_results = []
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            print(f"Fetching {key} page {page}...")
            response = await client.post(GRAPHQL_URL, json={"query": query, "variables": {"page": page}})
            data = response.json()
            
            if "errors" in data:
                print(f"Error fetching {key}: {data['errors']}")
                break
                
            results = data["data"][key]["results"]
            all_results.extend(results)
            
            if not data["data"][key]["info"]["next"]:
                break
            page += 1
    return all_results

def create_documents(characters: List[Dict], locations: List[Dict]) -> List[Document]:
    docs = []
    
    for char in characters:
        content = (
            f"Character: {char['name']}\n"
            f"Status: {char['status']}\n"
            f"Species: {char['species']}\n"
            f"Type: {char['type']}\n"
            f"Gender: {char['gender']}\n"
            f"Origin: {char['origin']['name']}\n"
            f"Location: {char['location']['name']}"
        )
        metadata = {
            "id": char["id"],
            "type": "character",
            "name": char["name"]
        }
        docs.append(Document(page_content=content, metadata=metadata))
        
    for loc in locations:
        resident_names = ", ".join([r["name"] for r in loc["residents"][:5]]) # Limit residents to avoid huge text
        if len(loc["residents"]) > 5:
            resident_names += f" and {len(loc['residents']) - 5} others"
            
        content = (
            f"Location: {loc['name']}\n"
            f"Type: {loc['type']}\n"
            f"Dimension: {loc['dimension']}\n"
            f"Residents: {resident_names}"
        )
        metadata = {
            "id": loc["id"],
            "type": "location",
            "name": loc["name"]
        }
        docs.append(Document(page_content=content, metadata=metadata))
        
    return docs

async def main():
    print("Starting indexing process...")
    
    # 1. Fetch Data
    characters = await fetch_all_pages(QUERY_CHARACTERS, "characters")
    locations = await fetch_all_pages(QUERY_LOCATIONS, "locations")
    
    print(f"Fetched {len(characters)} characters and {len(locations)} locations.")
    
    # 2. Create Documents
    docs = create_documents(characters, locations)
    print(f"Created {len(docs)} documents.")
    
    # 3. Embed and Index
    print("Embedding documents...")
    
    jina_key = os.environ.get("JINA_API_KEY")
    if not jina_key:
        print("❌ Error: JINA_API_KEY not found in environment or secrets.toml.")
        print("Please add it to .streamlit/secrets.toml and try again.")
        return

    embeddings = JinaEmbeddings(
        jina_api_key=jina_key, model_name="jina-embeddings-v2-base-en"
    )
    
    # Jina usually has better rate limits, but we'll still batch slightly
    batch_size = 100 
    vector_store = None
    
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1} ({len(batch)} docs)...")
        
        if vector_store is None:
            vector_store = FAISS.from_documents(batch, embeddings)
        else:
            vector_store.add_documents(batch)
    
    # 4. Save Index
    output_dir = os.path.join(os.path.dirname(__file__), "vector_store")
    vector_store.save_local(output_dir)
    print(f"Index saved to {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())
