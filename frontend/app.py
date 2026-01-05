import streamlit as st
import httpx
import asyncio
import json

# Configuration
BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Rick & Morty AI Explorer", layout="wide")

st.title("🧪 Rick & Morty AI Explorer")

# Sidebar for status
st.sidebar.header("System Status")

async def check_backend_status():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, "Backend returned error"
    except Exception as e:
        return False, str(e)

# Run the check
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

is_healthy, details = loop.run_until_complete(check_backend_status())

if is_healthy:
    st.sidebar.success("Backend Connected ✅")
else:
    st.sidebar.error("Backend Disconnected ❌")
    st.stop()

# --- Phase 2: Data & Interaction ---

async def get_locations(page=1):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/locations", params={"page": page})
        return resp.json()

async def get_notes(character_id):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BACKEND_URL}/notes/{character_id}")
        return resp.json()

async def get_notes_bulk(character_ids):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BACKEND_URL}/notes/bulk", json=character_ids)
        return resp.json()

async def add_note(character_id, content):
    async with httpx.AsyncClient() as client:
        await client.post(f"{BACKEND_URL}/notes", json={"character_id": character_id, "content": content})

async def generate_summary_stream(name, type, residents):
    # Increased timeout to 60 seconds to accommodate multiple LLM calls (generation + evaluation)
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=None)) as client:
        async with client.stream("POST", f"{BACKEND_URL}/generate-summary", json={
            "name": name,
            "type": type,
            "residents": residents
        }) as response:
            async for chunk in response.aiter_text():
                yield chunk

# Layout
tab1, tab2 = st.tabs(["🌍 Locations Explorer", "🔍 Semantic Search"])

with tab1:
    st.header("Locations")

    # Pagination (Simple)
    page = st.number_input("Page", min_value=1, value=1)

    locations = loop.run_until_complete(get_locations(page))

    # --- OPTIMIZATION START ---
    # 1. Collect all resident IDs first
    all_resident_ids = []
    if locations:
        for loc in locations:
            for res in loc.get("residents", []):
                all_resident_ids.append(res['id'])

    # 2. Fetch all notes in ONE request
    notes_map = {}
    if all_resident_ids:
        notes_map = loop.run_until_complete(get_notes_bulk(all_resident_ids))
    # --- OPTIMIZATION END ---

    if not locations:
        st.warning("No locations found.")
    else:
        for loc in locations:
            with st.expander(f"{loc['name']} ({loc['type']})"):
                st.write(f"**Dimension:** {loc['dimension']}")
                
                # AI Summary Section
                if st.button(f"😎 Tour this Location", key=f"ai_{loc['id']}"):
                    with st.spinner("Rick is thinking... (or drinking)"):
                        st.markdown("### 🗣️ Narrator's Take")
                        summary_placeholder = st.empty()
                        # Use a mutable container to avoid scoping issues
                        state = {"full_summary": "", "evaluation_data": None}
                        
                        # Consume the stream
                        async def run_stream():
                            accumulated = ""
                            async for chunk in generate_summary_stream(loc['name'], loc['type'], loc['residents']):
                                accumulated += chunk
                                if "|||" in accumulated:
                                    parts = accumulated.split("|||")
                                    state["full_summary"] = parts[0]
                                    summary_placeholder.info(state["full_summary"])
                                    if len(parts) > 1 and parts[1]:
                                        try:
                                            state["evaluation_data"] = json.loads(parts[1])
                                        except:
                                            pass
                                else:
                                    state["full_summary"] = accumulated
                                    summary_placeholder.info(state["full_summary"])
                        
                        loop.run_until_complete(run_stream())
                        
                        if state["evaluation_data"]:
                            st.markdown("### ⚖️ AI Evaluation")
                            col_score, col_reason = st.columns([1, 4])
                            col_score.metric("Consistency Score", f"{state['evaluation_data']['score']}/10")
                            col_reason.write(f"**Reasoning:** {state['evaluation_data']['reasoning']}")
                
                residents = loc.get("residents", [])
                if residents:
                    st.subheader("Residents")
                    cols = st.columns(3)
                    for idx, res in enumerate(residents):
                        with cols[idx % 3]:
                            st.image(res['image'], width=100)
                            st.write(f"**{res['name']}**")
                            st.caption(f"{res['status']} - {res['species']}")
                            
                            # Notes Section
                            with st.popover(f"📝 Notes for {res['name']}"):
                                # Use the pre-fetched notes from memory
                                notes = notes_map.get(res['id'], [])
                                
                                if notes:
                                    st.markdown("---")
                                    for n in notes:
                                        st.text(f"• {n['content']}")
                                    st.markdown("---")
                                
                                # Add new note
                                new_note = st.text_input(f"Add note", key=f"note_{res['id']}")
                                if st.button("Save", key=f"save_{res['id']}"):
                                    if new_note:
                                        loop.run_until_complete(add_note(res['id'], new_note))
                                        st.success("Saved!")
                                        st.rerun()
                else:
                    st.info("No residents listed.")

with tab2:
    st.header("🔍 Semantic Search")
    st.write("Search the Rick & Morty universe using natural language.")
    
    query = st.text_input("What are you looking for?", placeholder="e.g., 'A planet with screaming suns' or 'Rick's best friend'")
    
    if query:
        if st.button("Search"):
            with st.spinner("Searching the multiverse..."):
                async def perform_search():
                    # Increased timeout to 30s for embedding generation and index search
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(f"{BACKEND_URL}/search", json={"query": query})
                        return resp.json()
                
                results = loop.run_until_complete(perform_search())
                
                results = loop.run_until_complete(perform_search())
                
                found_chars = results.get("characters", [])
                found_locs = results.get("locations", [])
                
                if not found_chars and not found_locs:
                    st.info("No results found in this dimension.")
                else:
                    # Pre-fetch notes for all relevant characters
                    search_resident_ids = []
                    # 1. IDs from direct character results
                    for c in found_chars:
                        search_resident_ids.append(c['id'])
                    # 2. IDs from residents in location results
                    for l in found_locs:
                        for r in l.get("residents", []):
                            search_resident_ids.append(r['id'])
                    
                    search_notes_map = {}
                    if search_resident_ids:
                        search_notes_map = loop.run_until_complete(get_notes_bulk(search_resident_ids))

                    # --- Display Characters ---
                    if found_chars:
                        st.subheader("Characters")
                        cols = st.columns(3)
                        for idx, res in enumerate(found_chars):
                            with cols[idx % 3]:
                                st.image(res['image'], width=100)
                                st.write(f"**{res['name']}**")
                                st.caption(f"{res['status']} - {res['species']}")
                                
                                # Notes Section
                                with st.popover(f"📝 Notes for {res['name']}"):
                                    notes = search_notes_map.get(res['id'], [])
                                    if notes:
                                        st.markdown("---")
                                        for n in notes:
                                            st.text(f"• {n['content']}")
                                        st.markdown("---")
                                    
                                    new_note = st.text_input(f"Add note", key=f"search_note_in_{res['id']}")
                                    if st.button("Save", key=f"search_save_{res['id']}"):
                                        if new_note:
                                            loop.run_until_complete(add_note(res['id'], new_note))
                                            st.success("Saved!")
                                            st.rerun()
                        st.divider()

                    # --- Display Locations ---
                    if found_locs:
                        st.subheader("Locations")
                        for loc in found_locs:
                            with st.expander(f"{loc['name']} ({loc['type']})"):
                                st.write(f"**Dimension:** {loc['dimension']}")
                                
                                # AI Summary Section (Reused Logic)
                                if st.button(f"😎 Tour this Location", key=f"search_ai_{loc['id']}"):
                                    with st.spinner("Rick is thinking..."):
                                        st.markdown("### 🗣️ Narrator's Take")
                                        summary_placeholder = st.empty()
                                        state = {"full_summary": "", "evaluation_data": None}
                                        
                                        async def run_stream():
                                            accumulated = ""
                                            async for chunk in generate_summary_stream(loc['name'], loc['type'], loc['residents']):
                                                accumulated += chunk
                                                if "|||" in accumulated:
                                                    parts = accumulated.split("|||")
                                                    state["full_summary"] = parts[0]
                                                    summary_placeholder.info(state["full_summary"])
                                                    if len(parts) > 1 and parts[1]:
                                                        try:
                                                            state["evaluation_data"] = json.loads(parts[1])
                                                        except:
                                                            pass
                                                else:
                                                    state["full_summary"] = accumulated
                                                    summary_placeholder.info(state["full_summary"])
                                        
                                        loop.run_until_complete(run_stream())
                                        
                                        if state["evaluation_data"]:
                                            st.markdown("### ⚖️ AI Evaluation")
                                            col_score, col_reason = st.columns([1, 4])
                                            col_score.metric("Consistency Score", f"{state['evaluation_data']['score']}/10")
                                            col_reason.write(f"**Reasoning:** {state['evaluation_data']['reasoning']}")

                                residents = loc.get("residents", [])
                                if residents:
                                    st.write("**Residents:**")
                                    r_cols = st.columns(3)
                                    for r_idx, res in enumerate(residents):
                                        with r_cols[r_idx % 3]:
                                            st.image(res['image'], width=80)
                                            st.caption(f"{res['name']}")
                                else:
                                    st.info("No residents listed.")
