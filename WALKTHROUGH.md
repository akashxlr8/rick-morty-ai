# 🧪 Rick & Morty AI Explorer - Project Walkthrough

This document provides a technical deep-dive into the codebase, explaining how the different components interact to create the AI-powered explorer.

## 🏗️ Architecture Overview

The application follows a **Microservices-lite** architecture:

1.  **Frontend (Streamlit)**: Handles UI, user state, and displays data. It communicates with the backend via HTTP requests.
2.  **Backend (FastAPI)**: The brain of the operation. It handles:
    *   Data fetching from the external Rick & Morty GraphQL API.
    *   AI generation (LangChain + OpenAI).
    *   Semantic Search (Jina AI + FAISS).
    *   Cloud persistence for user notes (Supabase).
3.  **Data Layer**:
    *   **External**: [Rick & Morty GraphQL API](https://rickandmortyapi.com/graphql) (Source of Truth).
    *   **Vector Store**: Local FAISS index for semantic search.
    *   **Database**: Supabase (PostgreSQL) for user-generated notes.

---

## 📂 Directory Structure & Key Files

### 1. Backend (`/backend`)

*   **`main.py`**: The entry point for the FastAPI server.
    *   Defines API endpoints (`/locations`, `/generate-summary`, `/search`, `/notes`).
    *   Handles startup tasks like initializing the database and loading the vector index.
    *   **Key Feature**: Uses `StreamingResponse` for the AI narrator to stream text token-by-token to the frontend.

*   **`ai_service.py`**: Contains all AI logic.
    *   **`generate_location_summary_stream`**: Uses LangChain to create a streaming agent that narrates location details in the style of a cynical Rick & Morty character.
    *   **`evaluate_summary`**: A "Critic" model that checks the generated summary against factual data to ensure no hallucinations (e.g., inventing residents).
    *   **`search_knowledge_base`**: Handles embedding queries via Jina AI and searching the local FAISS index.

*   **`client.py`**: The Data Fetcher.
    *   Contains raw GraphQL queries to fetch characters and locations from the official API.
    *   Handles batch fetching (`fetch_characters_by_ids`) to optimize performance.

*   **`build_index.py`**: The Indexer Script.
    *   **Run once** to scrape the API and build the vector database.
    *   Uses `JinaEmbeddings` to convert text descriptions of characters/locations into vectors.
    *   Saves the result to `backend/vector_store/`.

*   **`database.py`**: Supabase client wrapper.
    *   Manages the `notes` table using the `supabase` Python client.

### 2. Frontend (`/frontend`)

*   **`app.py`**: The entire UI logic.
    *   **Tabs**: Splits the UI into "Locations Explorer" and "Semantic Search".
    *   **Async/Await**: Uses `asyncio` and `httpx` to make non-blocking calls to the backend.
    *   **State Management**: Uses `st.session_state` (implicitly via widgets) and mutable dictionaries to handle streaming data updates without refreshing the page.
    *   **Optimizations**: Implements "N+1" query prevention by batch-fetching all user notes for a page in a single request.

### 3. Configuration (`/.streamlit`)

*   **`secrets.toml`**: Stores sensitive API keys (`OPENAI_API_KEY`, `JINA_API_KEY`). **Never commit this file.**

---

## 🚀 Key Features Explained

### 🧠 1. The AI Narrator (Streaming)
*   **Flow**: User clicks "Tour this Location" -> Frontend calls `/generate-summary`.
*   **Backend**:
    1.  Constructs a prompt with the location's real data (residents, type).
    2.  Calls OpenAI via LangChain.
    3.  **Yields** chunks of text immediately as they are generated.
*   **Frontend**: Consumes the Server-Sent Events (SSE) and updates the text box in real-time, creating a "typing" effect.

### 🔍 2. Semantic Search (RAG - Retrieval Augmented Generation)
*   **Problem**: The official API only supports exact name matching (e.g., "Rick"). You can't search for "Rick's best friend".
*   **Solution**:
    1.  **Indexing**: We embedded descriptions of all characters/locations into a vector space.
    2.  **Search**: When you query "Rick's best friend", Jina converts that to a vector.
    3.  **Retrieval**: FAISS finds the closest vector (e.g., "Birdperson").
    4.  **Enrichment**: The backend takes the ID found by FAISS and fetches the latest image/status from the GraphQL API to display a rich card.

### 📝 3. Notes System
*   Allows users to attach private notes to specific characters.
*   Stored in Supabase (PostgreSQL).
*   **Optimization**: When loading a list of residents, the frontend sends *all* their IDs to `/notes/bulk` to get all notes in one go, rather than making 50 separate requests.

---
