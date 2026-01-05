import os
import json
from typing import List, Dict
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM using the new init_chat_model pattern from the docs
summary_model = init_chat_model("gpt-4o-mini", temperature=0.7)
critica_model = init_chat_model("gpt-5-nano", temperature=0)

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
    
    Data (Actual Residents): {", ".join(resident_names)}
    Generated Summary:</summary> {summary} </summary>
    """
    
    evaluation = await structured_llm.ainvoke(prompt)
    
    # with_structured_output returns the Pydantic object directly
    return evaluation.model_dump()
