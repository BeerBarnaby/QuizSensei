"""
Verification script for QuizSensei OCR System.
Mocks internal dependencies to test logic flow.
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.append("d:/Project/Nectec26")

def log(msg):
    print(msg)
    with open("debug_ocr.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def test_ocr_logic():
    log("[OCR] Starting OCR Logic Verification...")
    
    try:
        # Mocking settings and LLM calls
        mock_settings = MagicMock()
        mock_settings.OCR_MIN_TEXT_LENGTH = 100
        mock_settings.TESSERACT_CMD = "tesseract"
        mock_settings.VISION_LLM_MODEL = "mock-vision-model"
        mock_settings.openrouter_keys_list = ["key1"]
        mock_settings.OPENROUTER_BASE_URL = "http://mock"

        log("Patching get_settings...")
        with patch("app.core.config.get_settings", return_value=mock_settings):
            from app.services.ocr_service import OCRService
            
            ocr = OCRService()
            log(f"OCRService initialized. Sample text check: {await ocr.refine_content('short')} (expected 'short')")
            
            # 1. Test Refinement (Mock LLM)
            log("Test 1: Content Refinement...")
            # We must patch where it's used, or use the global mock if it's already imported.
            # Since ocr_service.py does 'from app.core.llm import call_openrouter_text', 
            # the reference to the function is already in ocr_service namespace.
            with patch("app.services.ocr_service.call_openrouter_text", new_callable=AsyncMock) as mock_refine:
                mock_refine.return_value = "### Refined Content\nThis is a test."
                test_input = "This is a long enough raw text for refinement."
                log(f"Calling refine_content with {len(test_input)} chars...")
                result = await ocr.refine_content(test_input)
                log(f"Refinement result: '{result}'")
                assert "### Refined Content" in result
                log("✅ Refinement Logic OK")

            # 2. Test Vision OCR (Mock HTTPX)
            log("Test 2: Vision OCR Logic...")
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_response = AsyncMock()
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Vision extracted text"}}]
                }
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response
                
                log("Calling extract_from_image_vision...")
                result = await ocr.extract_from_image_vision(b"fake-image-bytes")
                log(f"Vision result: '{result}'")
                assert result == "Vision extracted text"
                log("✅ Vision OCR Logic OK")

        log("\n🎉 All logic tests passed!")
    except Exception as e:
        log(f"❌ TEST FAILED: {type(e).__name__}: {e}")
        import traceback
        with open("debug_ocr.log", "a", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_ocr_logic())
