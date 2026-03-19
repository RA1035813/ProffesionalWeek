import requests
import json
import os
import sys

# Zorg dat we de rag_engine kunnen importeren, ook als we vanuit de root draaien
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from .rag_engine import SimpleRAG

# --- CONFIG ---
# Ollama draait standaard op localhost:11434
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral" 

def get_local_ai_advice(sensor_data, weather_data, system_prompt=None):
    """
    Roept de lokale Ollama instantie aan met RAG context.
    """
    rag = SimpleRAG(kb_path="localAI/knowledge_base.txt")
    extra_context = rag.get_relevant_context(sensor_data, weather_data)
    
    if not system_prompt:
        system_prompt = (
            "You are a professional agronomist for small-scale Tanzanian farmers. "
            "Use the following provided knowledge to generate a practical SMS advisory "
            "in simple English. Output ONLY the SMS content, no intro."
        )
    
    user_prompt = f"""
    KNOWLEDGE CONTEXT: {extra_context}
    SENSOR DATA: {sensor_data}
    WEATHER DATA: {weather_data}
    
    Produce a practical SMS report following these rules:
    - Write in plain English only
    - Structure: STATUS | NUTRIENTS | ACTION | PLANT | TIMING
    - Max 600 characters
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": system_prompt + "\n\n" + user_prompt,
        "stream": False,
        "options": {
            "num_predict": 300, 
            "temperature": 0.3 
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            advice = result.get("response", "").strip()
            # Forceer SMS lengte op 600
            return advice[:600]
        else:
            return f"Ollama Error: {response.status_code}"
    except Exception as e:
        print(f"Local AI Inference Error: {e}")
        return "Local AI unreachable. Check if Ollama is running."

if __name__ == "__main__":
    # Test call
    s = {'ph': 4.8, 'nitrogen_mg_kg': 40}
    w = {'precipitation_sum': [0.0]}
    print("Local AI SMS Output:")
    print(get_local_ai_advice(s, w))
