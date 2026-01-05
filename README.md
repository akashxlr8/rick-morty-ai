# Rick & Morty AI Explorer

## Setup & Run Instructions

### 1. Install Dependencies
Open a terminal in the project root:
```bash
pip install -r requirements.txt
```

### 2. Run the Backend (FastAPI)
Open a **new terminal** and run:
```bash
cd backend
uvicorn main:app --reload
```
*The backend will start at http://localhost:8000*

### 3. Run the Frontend (Streamlit)
Open a **second new terminal** and run:
```bash
cd frontend
streamlit run app.py
```
*The frontend will open in your browser (usually http://localhost:8501)*

## Project Structure
- `backend/`: FastAPI application (Data, Logic, AI)
- `frontend/`: Streamlit application (UI)

## Architectural Decisions & Trade-offs

### 1. Data Fetching: GraphQL vs. REST
**Decision:** Used the **GraphQL API** instead of standard REST endpoints.
**Reasoning:** The application requires displaying hierarchical data (Locations -> Residents -> Character Details).
- **REST approach:** Would require 1 call to get a location, then N calls for each resident URL found in that location (The "N+1" problem).
- **GraphQL approach:** Allows fetching a location and all its residents' specific fields (name, image, status) in a **single network request**, significantly reducing latency and bandwidth.

### 2. Backend Architecture: FastAPI + Streamlit
**Decision:** Decoupled the UI (Streamlit) from the Logic (FastAPI).
**Reasoning:**
- **Separation of Concerns:** The backend can evolve independently  and serves as a central API for both data and AI services. Streamlit is easy to configure and great for rapid prototyping of UIs.
- **Scalability:** If the app grows, the backend can be scaled separately (e.g., deployed on a cloud service) without affecting the frontend.
- **Streaming Support:** FastAPI's `StreamingResponse` enables real-time token streaming from the LLM to the frontend, improving perceived performance for the user.

### 3. Vector Store: FAISS (Local) vs. Managed Service
**Decision:** Used **FAISS** (Facebook AI Similarity Search) locally.
**Reasoning:**
- **Simplicity:** For a dataset of this size (~800 characters/locations), a local file-based index is instant and requires no external infrastructure setup or costs (unlike Pinecone or Weaviate).
- **Portability:** The index is built once and committed/distributed with the code, making the app easy to run locally.
- **Performance:** FAISS is optimized for fast similarity search and works well for the scale of this application.
- **JINA Integration:** Jina AI's embedding models API is free to use with SOTA like performance and generous limits, making it a cost-effective choice for generating embeddings without managing your own model.

### 4. Persistence: Supabase (PostgreSQL)
**Decision:** Migrated from SQLite to **Supabase**.
**Reasoning:**
- **Scalability:** Provides a robust, hosted PostgreSQL database that can handle more concurrent connections than a local SQLite file.
- **Remote Access:** Allows the database to be accessed from any deployed instance of the application, rather than being tied to the local filesystem.
- **Future-Proofing:** Enables easier addition of features like authentication and real-time subscriptions in the future.


### 5. AI Integration: LangChain + OpenAI
**Decision:** Used **LangChain** to orchestrate LLM calls with **OpenAI**
**Reasoning:**
- **Abstraction:** LangChain provides a high-level interface to manage prompts, agents, and chains, simplifying the integration of LLMs into the application.
- **Streaming Support:** LangChain's support for streaming responses allows for real-time narration, enhancing
    user experience.
- **Extensibility:** LangChain makes it easier to add more complex AI features in the future, such as multi-step reasoning or tool use. as well as manages single-provider lockin.