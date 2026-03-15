import json
import random
import logging
import requests
from typing import Dict, Any, Optional, List, Union
from app.core.config import get_settings

logger = logging.getLogger(__name__)

def get_llm_api_key() -> str:
    """Centralized API key selection logic."""
    settings = get_settings()
    keys = settings.openrouter_keys_list
    return random.choice(keys) if keys else "dummy"

def clean_json_string(raw: str) -> str:
    """Removes markdown code fences and extraneous text from LLM responses."""
    if not raw:
        return ""
    # Remove markdown code fences if present
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return raw.strip()

def call_openrouter_completions(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4000,
    timeout: int = 180
) -> Optional[str]:
    """
    Centralized utility to call OpenRouter API using the v1/completions endpoint.
    Handles key selection and basic text retrieval.
    """
    settings = get_settings()
    api_key = get_llm_api_key()
    target_model = model or settings.OPENROUTER_MODEL
    
    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/QuizSensei/Nectec26",
        "X-Title": "QuizSensei Assessment Platform"
    }

    payload = {
        "model": target_model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code != 200:
            logger.error(f"LLM API Error: {response.status_code} - {response.text}")
            return None

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            # Handle both completions (.text) and chat-completions fallback (.message.content)
            raw_text = choice.get("text") or choice.get("message", {}).get("content")
            return raw_text.strip() if raw_text else None
        
        logger.error(f"Unexpected Response Format: {result}")
        return None

    except Exception as e:
        logger.error(f"LLM Connection failed: {e}")
        return None

def call_openrouter_json(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4000
) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Calls completions, cleans markdown fences, and parses JSON result."""
    raw = call_openrouter_completions(prompt, model, temperature, max_tokens)
    if not raw:
        return None
        
    cleaned = clean_json_string(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}\nRaw content: {raw[:500]}")
        return None

def call_openrouter_vision(
    prompt: str,
    base64_image: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    timeout: int = 120
) -> Optional[str]:
    """Centralized vision utility for OCR."""
    settings = get_settings()
    api_key = get_llm_api_key()
    target_model = model or settings.OPENROUTER_MODEL_OCR
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/QuizSensei/Nectec26",
        "X-Title": "QuizSensei Assessment Platform"
    }

    payload = {
        "model": target_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "temperature": temperature
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code != 200:
            logger.warning(f"Vision API Error: {response.text}")
            return None

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        return None
    except Exception as e:
        logger.error(f"Vision call aborted: {e}")
        return None
