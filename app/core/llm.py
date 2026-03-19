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
    """
    Removes markdown code fences and extraneous text from LLM responses.
    Ensures the string passed to json.loads is a clean JSON structure.
    """
    if not raw:
        return ""
    # Extract content inside ```json ... ``` or just ``` ... ```
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return raw.strip()

def call_openrouter_text(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4000
) -> Optional[str]:
    """
    Centralized utility to call OpenRouter API with key rotation and standard headers.
    """
    settings = get_settings()
    api_key = get_llm_api_key()
    if not api_key or api_key == "dummy":
        logger.error("No valid OPENROUTER_API_KEYS found in settings.")
        return None

    target_model = model or settings.OPENROUTER_MODEL
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/BeerBarnaby/Nectec26",
        "X-Title": "QuizSensei AI Platform",
    }
    
    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    logger.info(f"--- LLM REQUEST (TEXT) ---")
    logger.info(f"MODEL: {target_model}")
    logger.info(f"PROMPT (first 250 characters): {prompt[:250]}...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            logger.error(f"LLM API Error {response.status_code}: {response.text}")
            return None
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "error" in choice:
                logger.error(f"LLM Provider Error: {choice['error']}")
                return None
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"].strip()
                logger.info(f"--- LLM RESPONSE (TEXT) RECEIVED ---")
                logger.info(f"CONTENT (first 250 characters): {content[:250]}...")
                return content
            if "text" in choice:
                content = choice["text"].strip()
                logger.info(f"--- LLM RESPONSE (TEXT) RECEIVED ---")
                logger.info(f"CONTENT (first 250 characters): {content[:250]}...")
                return content
        
        logger.error(f"LLM API returned no choices: {result}")
        return None
    except Exception as e:
        logger.error(f"LLM Connection failed ({target_model}): {e}")
        return None

def call_openrouter_json(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 8000
) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    Calls LLM with JSON mode enabled via response_format. 
    Includes fallback 'scavenger' for parsing failures.
    """
    settings = get_settings()
    api_key = get_llm_api_key()
    if not api_key or api_key == "dummy":
        return None

    target_model = model or settings.OPENROUTER_MODEL
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/BeerBarnaby/Nectec26",
        "X-Title": "QuizSensei AI Platform",
    }
    
    # Force JSON in prompt and via API parameter
    json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON."
    
    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": json_prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }

    logger.info(f"--- LLM REQUEST (JSON MODE) ---")
    logger.info(f"MODEL: {target_model}")
    logger.info(f"PROMPT (first 250 characters): {json_prompt[:250]}...")

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            logger.error(f"LLM JSON API Error {response.status_code}: {response.text}")
            return None
            
        result = response.json()
        if "choices" not in result or not result["choices"]:
            return None
            
        choice = result["choices"][0]
        if "error" in choice:
            logger.error(f"LLM JSON Provider Error: {choice['error']}")
            return None

        raw = choice.get("message", {}).get("content", "").strip()
        if not raw:
            raw = choice.get("text", "").strip()
            
        if not raw:
            return None

        cleaned = clean_json_string(raw)
        logger.info(f"--- LLM RESPONSE (JSON) RECEIVED ---")
        logger.info(f"CLEANED CONTENT (first 250 characters): {cleaned[:250]}...")
        
        try:
            parsed = json.loads(cleaned)
            logger.info(f"PARSED SUCCESS: Keys found: {list(parsed.keys()) if isinstance(parsed, dict) else 'List'}")
            return parsed
        except Exception as e:
            logger.error(f"JSON Parse Error: {e}")
            logger.error(f"Raw Response: {raw}")
            
            # ── Scavenging fallback with Heuristic Repair ──────────────────
            try:
                # 1. Basic block extraction
                start_idx = max(cleaned.find('['), cleaned.find('{'))
                if start_idx == -1: return None
                
                salvaged = cleaned[start_idx:].strip()
                
                # 2. Heuristic repair for truncated JSON
                # If it doesn't end correctly, try to close it
                if not (salvaged.endswith('}') or salvaged.endswith(']')):
                    # Try to close a dangling string if odd number of quotes
                    if salvaged.count('"') % 2 != 0:
                        salvaged += '"'
                    
                    # Naively close braces in reverse order
                    # (Better than nothing for truncation)
                    stack = []
                    for char in salvaged:
                        if char == '{': stack.append('}')
                        elif char == '[': stack.append(']')
                        elif char == '}' and stack and stack[-1] == '}': stack.pop()
                        elif char == ']' and stack and stack[-1] == ']': stack.pop()
                    
                    while stack:
                        salvaged += stack.pop()
                
                return json.loads(salvaged)
            except Exception:
                # One last attempt: find the last valid object in a list if it was a list
                try:
                    # If it's a truncated list, maybe we have at least one valid object
                    if cleaned.strip().startswith('['):
                        valid_part = cleaned[:cleaned.rfind('}')+1]
                        if valid_part:
                            if not valid_part.endswith(']'): valid_part += ']'
                            return json.loads(valid_part)
                except Exception: pass
            return None
            
    except Exception as e:
        logger.error(f"LLM JSON Connection failed: {e}")
        return None
