import json
import logging
from typing import List, Dict, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def _call_gemini(prompt: str) -> str:
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
        raise ValueError("Gemini API key is not configured or is the default placeholder.")
    return _call_gemini_api(prompt)

@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=2, min=5, max=60), reraise=True)
def _call_gemini_api(prompt: str) -> str:
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(prompt)
    return response.text

def classify_transactions(uncategorised_txns: List[Dict]) -> Tuple[List[Dict], str, bool]:
    """
    Takes a list of transaction dicts, calls LLM, and returns updated dicts + raw response.
    Returns (updated_txns, raw_response, llm_failed)
    """
    if not uncategorised_txns:
        return [], "", False
        
    prompt = f"""You are a financial transaction classifier. For each transaction below, assign exactly
one category from the following list: Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other.

You MUST respond ONLY with a valid JSON array of objects, with no markdown formatting.
Each object must have "txn_idx" (integer) and "category" (string).

Transactions:
"""
    for i, txn in enumerate(uncategorised_txns):
        prompt += f"{i}. merchant={txn.get('merchant')}, amount={txn.get('amount')}, notes={txn.get('notes')}\n"
        
    try:
        raw_response = _call_gemini(prompt)
        

        cleaned_response = raw_response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
            
        results = json.loads(cleaned_response)
        

        for item in results:
            idx = item.get('txn_idx')
            if idx is not None and 0 <= idx < len(uncategorised_txns):
                uncategorised_txns[idx]['llm_category'] = item.get('category')
                
        return uncategorised_txns, raw_response, False
        
    except Exception as e:
        logger.error(f"LLM classification failed: {str(e)}")
        return uncategorised_txns, str(e), True

def generate_narrative(aggregates: Dict) -> Tuple[Dict, str, bool]:
    """
    Calls LLM to generate summary narrative and risk level.
    Returns (summary_dict, raw_response, llm_failed)
    """
    prompt = f"""Given the following financial transaction summary, produce a JSON response with:
- narrative: A 2-3 sentence spending narrative describing the patterns.
- risk_level: "low", "medium", or "high" based on the anomaly count and spending patterns.

You MUST respond ONLY with a valid JSON object, with no markdown formatting.

Data:
{json.dumps(aggregates, indent=2)}
"""
    try:
        raw_response = _call_gemini(prompt)
        
        cleaned_response = raw_response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
            
        result = json.loads(cleaned_response)
        
        return {
            "narrative": result.get("narrative"),
            "risk_level": result.get("risk_level")
        }, raw_response, False
        
    except Exception as e:
        logger.error(f"LLM narrative generation failed: {str(e)}")
        return {"narrative": None, "risk_level": None}, str(e), True

