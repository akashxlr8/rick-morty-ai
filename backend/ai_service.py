import os
import json
import toml
from typing import List, Dict
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_community.embeddings import JinaEmbeddings
from langchain_community.vectorstores import FAISS

# Try to load secrets if env var is missing
try:
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "OPENAI_API_KEY" in secrets and "OPENAI_API_KEY" not in os.environ:
            os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
        if "JINA_API_KEY" in secrets and "JINA_API_KEY" not in os.environ:
            os.environ["JINA_API_KEY"] = secrets["JINA_API_KEY"]
except Exception:
    pass

# Initialize LLM using the new init_chat_model pattern from the docs
summary_model = init_chat_model("gpt-4o-mini", temperature=0.85)
critica_model = init_chat_model("gpt-5-nano", temperature=0)

_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        index_path = os.path.join(os.path.dirname(__file__), "vector_store")
        if os.path.exists(index_path):
            jina_key = os.environ.get("JINA_API_KEY")
            if not jina_key:
                print("❌ Error: JINA_API_KEY not found in environment.")
                return None
                
            embeddings = JinaEmbeddings(
                jina_api_key=jina_key, model_name="jina-embeddings-v2-base-en"
            )
            _vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            print(f"✅ Vector store loaded with {_vector_store.index.ntotal} documents.")
    return _vector_store

async def search_knowledge_base(query: str, k: int = 4):
    """Searches the vector store for relevant documents."""
    vector_store = get_vector_store()
    if not vector_store:
        print("⚠️ Vector store not found or failed to load.")
        return []
    
    print(f"🔍 Embedding query: '{query}'")
    docs = vector_store.similarity_search(query, k=k)
    print(f"✅ Found {len(docs)} documents.")
    return [{"content": d.page_content, "metadata": d.metadata} for d in docs]

class EvaluationResponse(BaseModel):
    """Response schema for the evaluation."""
    score: int = Field(description="A score from 0 to 10 for factual consistency.")
    reasoning: str = Field(description="Explanation for the score, specifically checking if it mentioned characters not present in the data.")

async def generate_location_summary_stream(location_name: str, location_type: str, residents: List[Dict]):
    """Generates a summary in the tone of a Rick & Morty narrator, yielding tokens."""
    
    resident_names = [r['name'] for r in residents]
    resident_str = ", ".join(resident_names) if resident_names else "no one (it's empty, Morty!)"
    
    system_prompt = """You are the cynical, sci-fi narrator from the Rick & Morty universe. 
    Describe the following location and its inhabitants. 
    Be humorous, slightly dark, and use show-accurate language (e.g., mentioning multi-verses, pointless existence, etc.).
    Write a 4–6 sentence travel guide for this location.
    Mention the location name and type.
    Reference at least one of the residents by name.
    Give a “danger rating” from 1–10 at the end, with a  witty under-10 worded comment on why.
    Keep it in Rick & Morty style humor, but do not invent new canon facts.
    
    Example:
    <example>   
    Travel Guide to Anatomy Park: A Microverse of Maladies

    Welcome to Anatomy Park, a twisted microverse nestled within the crowded confines of a human body! Here, you can take a thrilling tour through the inner workings of a human, complete with disease-themed attractions that are sure to make your insides churn—literally! Meet Dr. Xenon Bloom, the über-enthusiastic, somewhat questionable guide who's always one misstep away from an existential crisis. You’ll also encounter charming residents like Tuberculosis and Gonorrhea, who are just dying—pun intended—to show you a good time. Just remember, every ride is a potential trip to the ER, so pack your medical insurance and a sense of humor.

    Danger Rating: 8/10 - Because who needs a healthy immune system anyway?
    </example>

    Here is the data you have:
    """

    agent = create_agent(
        model=summary_model,
        system_prompt=system_prompt,
    )
    
    input_msg = f"Location Name: {location_name}\nLocation Type: {location_type}\nKnown Residents: {resident_str}"
    
    full_summary = ""

    async for event in agent.astream(
        {"messages": [{"role": "user", "content": input_msg}]},
        stream_mode="messages"
    ):
        message = event[0]
        # Relaxed check: if it has content, yield it.
        if hasattr(message, "content") and message.content:
            content = message.content
            full_summary += content
            yield content
    
    # After summary is done, run evaluation
    evaluation = await evaluate_summary(full_summary, residents)
    # Yield a separator and the evaluation JSON
    yield f"|||{json.dumps(evaluation)}"

async def generate_location_summary(location_name: str, location_type: str, residents: List[Dict]):
    """Generates a summary in the tone of a Rick & Morty narrator."""
    # Re-using the stream logic to avoid duplication
    full_summary = ""
    async for chunk in generate_location_summary_stream(location_name, location_type, residents):
        if "|||" not in chunk:
            full_summary += chunk
    return full_summary

async def evaluate_summary(summary: str, original_residents: List[Dict]):
    """Evaluates the summary for factual consistency using the modern with_structured_output pattern."""
    
    resident_names = [r['name'] for r in original_residents]
    
    # Use with_structured_output as it's the modern replacement for StructuredOutputParser
    structured_llm = critica_model.with_structured_output(EvaluationResponse)
    
    prompt = f"""
    You are an objective evaluator. Your task is to check if the following AI-generated summary is factually consistent with the provided data.
    
    Data (Actual Residents): {", ".join(resident_names) if resident_names else "None listed (The location might be empty or data is missing)."}
    Generated Summary:</summary> {summary} </summary>

    Rules:
    1. If the Data list is empty, do NOT penalize the summary for describing the location's atmosphere, history, or general vibe.
    2. Only penalize if the summary explicitly names specific characters as *current residents* who are not in the Data list.
    3. References to "Morty" or "Rick" as part of the narration style (e.g. "It's boring, Morty!") are allowed and should NOT be counted as factual errors.
    """
    
    evaluation = await structured_llm.ainvoke(prompt)
    
    # with_structured_output returns the Pydantic object directly
    return evaluation.model_dump()
