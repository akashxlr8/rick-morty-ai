import streamlit as st
import httpx
import asyncio

# Configuration
BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Rick & Morty AI Explorer", layout="wide")

st.title("🧪 Rick & Morty AI Explorer")

st.markdown("""
Welcome to the AI-powered explorer for the Rick & Morty universe.
This frontend connects to a FastAPI backend for data processing and AI generation.
""")

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
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
is_healthy, details = loop.run_until_complete(check_backend_status())

if is_healthy:
    st.sidebar.success("Backend Connected ✅")
    st.sidebar.json(details)
else:
    st.sidebar.error("Backend Disconnected ❌")
    st.sidebar.warning(f"Make sure the FastAPI server is running at {BACKEND_URL}")
    st.sidebar.code(f"Error: {details}")

st.divider()

st.info("Phase 1: Basic Connectivity Established. Use the sidebar to verify backend connection.")
