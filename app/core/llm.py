"""
Core LLM integration layer.
Provides utilities for communicating with OpenRouter APIs for completions and JSON extraction.
"""
import json
import random
import logging
import asyncio
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

def call_openrouter_text(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4000,
    timeout: int = 240,
    endpoint: str = "responses"
) -> Optional[str]:
    """
    Centralized utility to call OpenRouter API.
    By default uses /responses (optimized for StepFun).
    """
    settings = get_settings()
    api_key = get_llm_api_key()
    target_model = model or settings.OPENROUTER_MODEL
    
    url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # /responses API uses "input" field
    payload = {
        "model": target_model,
        "input": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    # If using chat/completions, transform payload
    if "chat/completions" in url:
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    logger.debug(f"LLM Request: {url} | Model: {target_model}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if response.status_code != 200:
            logger.error(f"LLM API Error {response.status_code}: {response.text}")
            return None

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            # Handle both text (Completions) and message content (Chat)
            if "text" in choice:
                return choice["text"].strip()
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
            
        return None
    except Exception as e:
        logger.error(f"LLM Connection failed: {e}")
        return None

# Backwards compatibility alias
def call_openrouter_completions(*args, **kwargs) -> Optional[str]:
    return call_openrouter_text(*args, **kwargs)

def call_openrouter_json(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4000
) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Calls LLM, cleans markdown fences, and parses JSON result."""
    raw = call_openrouter_text(prompt, model, temperature, max_tokens)
    if not raw:
        return None
        
    cleaned = clean_json_string(raw)
    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"JSON Parse Error: {e}")
        # Scavenging fallback
        try:
            start_idx = max(cleaned.find('['), cleaned.find('{'))
            end_idx = max(cleaned.rfind(']'), cleaned.rfind('}'))
            if start_idx != -1 and end_idx != -1:
                return json.loads(cleaned[start_idx:end_idx+1])
        except:
            pass
        return None
