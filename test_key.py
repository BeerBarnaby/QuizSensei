import logging
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from app.core.llm import call_openrouter_json, get_llm_api_key
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestKey")

def test_llm():
    settings = get_settings()
    logger.info("--- Testing Centralized LLM Utility ---")
    
    prompt = "Create a JSON object with a 'message' field that says 'Ready to serve' in Thai."
    logger.info(f"Testing Prompt: {prompt}")
    
    # Test JSON/Completions
    result = call_openrouter_json(
        prompt=prompt,
        model=settings.OPENROUTER_MODEL,
        temperature=0.7
    )
    
    if result:
        logger.info(f"SUCCESS: Received JSON response: {json.dumps(result, ensure_ascii=False)}")
    else:
        logger.error("FAILED: Could not get valid JSON response from LLM utility.")

    key = get_llm_api_key()
    logger.info(f"Using API Key starting with: {key[:10]}...")

if __name__ == "__main__":
    test_llm()