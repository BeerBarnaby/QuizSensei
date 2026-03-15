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

    # ── [LOG BEFORE SENDING] ──────────────────────────────────────────
    logger.info("============== LLM REQUEST START ==============")
    logger.info(f"URL: {url}")
    logger.info(f"Model: {target_model}")
    logger.info(f"Prompt Length: {len(prompt)} chars")
    # logger.info(f"Full Prompt Sent:\n{prompt}") # Selective: can be very large
    logger.info("===============================================")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        
        # ── [LOG AFTER RECEIVING] ────────────────────────────────────────
        logger.info(f"LLM RESPONSE STATUS: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"LLM API Error Body: {response.text}")
            return None

        result = response.json()
        logger.info("============== LLM RESPONSE PARTIAL ==============")
        # Log first 500 chars of result for debugging
        logger.info(f"Raw JSON result keys: {list(result.keys())}")
        
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            raw_text = choice.get("text") or choice.get("message", {}).get("content")
            
            if raw_text:
                logger.info(f"Received Text Length: {len(raw_text)}")
                logger.info(f"Snippet (first 300): {raw_text[:300]}...")
                logger.info("================================================")
                return raw_text.strip()
            
        logger.error(f"No text found in response: {result}")
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
        logger.error("LLM returned no content or failed.")
        return None
        
    cleaned = clean_json_string(raw)
    try:
        data = json.loads(cleaned)
        logger.debug("Successfully parsed JSON from LLM.")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error @ {e.lineno}:{e.colno} - {e.msg}")
        logger.error(f"First 1000 chars of raw content: {raw[:1000]}")
        # Try to find the start of the JSON array/object if cleaning failed
        try:
            start_idx = cleaned.find('[') if '[' in cleaned else cleaned.find('{')
            end_idx = cleaned.rfind(']') if ']' in cleaned else cleaned.rfind('}')
            if start_idx != -1 and end_idx != -1:
                logger.info("Retrying JSON parse by finding delimiters...")
                return json.loads(cleaned[start_idx:end_idx+1])
        except:
            pass
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
