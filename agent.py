"""
AI Agent — Lead Scoring & Response Generation
Supports OpenAI API and local Ollama models
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Dict

from config import (
    AI_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL,
    OLLAMA_URL, OLLAMA_MODEL
)

logger = logging.getLogger(__name__)


LEAD_SCORING_PROMPT = """You are a business lead scoring AI agent. Analyze the following lead and provide:
1. A score from 1-10 (10 = highest quality lead)
2. A category: "hot", "warm", or "cold"
3. A brief analysis (1-2 sentences)
4. A suggested follow-up response (2-3 sentences, professional tone)

Lead Information:
- Name: {name}
- Email: {email}
- Company: {company}
- Message: {message}

Respond in JSON format only:
{{
    "score": <number 1-10>,
    "category": "<hot|warm|cold>",
    "analysis": "<brief analysis>",
    "response": "<suggested follow-up email>"
}}"""


CUSTOM_PROMPT_TEMPLATE = """You are a business automation AI assistant. 
Process the following data according to the instructions.

Instructions: {instructions}

Data:
{data}

Respond in JSON format only:
{{
    "result": "<processed result>",
    "confidence": <0.0-1.0>,
    "notes": "<any additional notes>"
}}"""


class AIAgent:
    """AI-powered lead scoring and response generation"""

    def __init__(self, provider: str = None):
        self.provider = provider or AI_PROVIDER
        logger.info(f"AI Agent initialized with provider: {self.provider}")

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = json.dumps({
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama API"""
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }).encode()

        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data.get("response", "")

    def _call_ai(self, prompt: str) -> str:
        """Route to the configured AI provider"""
        if self.provider == "openai":
            return self._call_openai(prompt)
        elif self.provider == "ollama":
            return self._call_ollama(prompt)
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    def _parse_json_response(self, response: str) -> Dict:
        """Extract JSON from AI response (handles markdown code blocks)"""
        text = response.strip()
        # Remove markdown code block if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response as JSON: {text[:200]}")
            return {"score": 5, "category": "warm", "analysis": text[:200], "response": ""}

    def score_lead(self, lead: Dict) -> Dict:
        """
        Score a lead using AI.
        Returns: {"score": int, "category": str, "analysis": str, "response": str}
        """
        prompt = LEAD_SCORING_PROMPT.format(
            name=lead.get("name", "Unknown"),
            email=lead.get("email", ""),
            company=lead.get("company", ""),
            message=lead.get("message", "")
        )

        try:
            raw_response = self._call_ai(prompt)
            result = self._parse_json_response(raw_response)

            # Validate score
            score = int(result.get("score", 5))
            score = max(1, min(10, score))
            result["score"] = score

            # Validate category
            if result.get("category") not in ("hot", "warm", "cold"):
                result["category"] = "hot" if score >= 8 else "warm" if score >= 5 else "cold"

            return result
        except Exception as e:
            logger.error(f"AI scoring failed for {lead.get('name')}: {e}")
            return {
                "score": 5,
                "category": "warm",
                "analysis": f"Error: {str(e)}",
                "response": ""
            }

    def process_custom(self, data: str, instructions: str) -> Dict:
        """Process custom data with custom instructions"""
        prompt = CUSTOM_PROMPT_TEMPLATE.format(
            instructions=instructions,
            data=data
        )
        try:
            raw_response = self._call_ai(prompt)
            return self._parse_json_response(raw_response)
        except Exception as e:
            logger.error(f"Custom processing failed: {e}")
            return {"result": f"Error: {str(e)}", "confidence": 0.0, "notes": ""}

    def classify_sentiment(self, text: str) -> str:
        """Quick sentiment classification"""
        prompt = f'Classify the sentiment of this text as "positive", "negative", or "neutral". Reply with one word only.\n\nText: {text}'
        try:
            result = self._call_ai(prompt).strip().lower()
            if result in ("positive", "negative", "neutral"):
                return result
            return "neutral"
        except Exception:
            return "neutral"
