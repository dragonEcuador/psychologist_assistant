import json
import re
import requests
from typing import Dict, Any, List, Optional
from langchain_ollama import ChatOllama

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:1b"

def check_ollama_status() -> Dict[str, Any]:
    """Checks connection to local Ollama server and lists available models."""
    try:
        res = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if res.status_code == 200:
            models_data = res.json().get("models", [])
            model_names = [m.get("name") for m in models_data]
            return {
                "online": True,
                "models": model_names,
                "error": None
            }
    except Exception as e:
        return {
            "online": False,
            "models": [],
            "error": str(e)
        }
    return {"online": False, "models": [], "error": "Unknown error"}

def get_available_model_name(preferred_model: str = DEFAULT_MODEL) -> str:
    status = check_ollama_status()
    models = status.get("models", [])
    if not models:
        return preferred_model
    
    # Check exact match or prefix match
    for m in models:
        if preferred_model in m or m in preferred_model:
            return m
    
    # Check common defaults
    for fallback in ["llama3.2:1b", "llama3.2", "llama3", "mistral", "phi3"]:
        for m in models:
            if fallback in m:
                return m
                
    return models[0]

def get_local_llm(model_name: Optional[str] = None, temperature: float = 0.1, max_tokens: int = 350) -> ChatOllama:
    selected_model = model_name if model_name else get_available_model_name()
    return ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=selected_model,
        temperature=temperature,
        num_predict=max_tokens,
        num_ctx=2048
    )

def clean_and_parse_json(text: str) -> Any:
    """Extracts and parses JSON object or array from LLM response text."""
    if not text:
        raise ValueError("Empty text received for JSON parsing")
    
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Regex search for json array [...] or json object {...}
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    # If parsing fails, clean common trailing commas or single quote issues
    cleaned_fuzzy = re.sub(r",\s*([\]}])", r"\1", cleaned)
    match = re.search(r"(\{.*\}|\[.*\])", cleaned_fuzzy, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
    raise ValueError(f"Could not parse valid JSON from response: {text[:200]}...")
