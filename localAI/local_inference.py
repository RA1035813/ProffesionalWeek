import requests
import json
from .rag_engine import SimpleRAG

# --- CONFIG ---
# Assuming Ollama is running on localhost:11434
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral" # Or llama3, mistral, or any light model you pulled

def get_local_ai_advice(sensor_data, weather_data):
    """
    Calls the local Ollama instance with RAG context.
    """
    rag = SimpleRAG()
    extra_context = rag.get_relevant_context(sensor_data, weather_data)
    
    system_instruction = (
        "You are a professional agronomist for small-scale Tanzanian farmers. "
        "Use the following provided knowledge to generate a 160-character SMS advisory "
        "in simple English or Swahili. Output ONLY the SMS content."
    )
    
    user_prompt = f"""
    KNOWLEDGE CONTEXT: {extra_context}
    SENSOR DATA: {sensor_data}
    WEATHER DATA: {weather_data}
    
    Actionable SMS Advisory (<160 chars):
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": system_instruction + "\n\n" + user_prompt,
        "stream": False,
        "options": {
            "num_predict": 100, # Limit response length
            "temperature": 0.4
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        result = response.json()
        return result.get("response", "System error. Please check soil manualy.").strip()[:160]
    except Exception as e:
        print(f"Local AI Inference Error: {e}")
        return "Local AI unreachable. Check Ollama status."

if __name__ == "__main__":
    # Test call
    s = {'ph': 4.8, 'nitrogen_mg_kg': 40}
    w = {'precipitation_sum': [0.0]}
    print("Local AI SMS Output:")
    print(get_local_ai_advice(s, w))
