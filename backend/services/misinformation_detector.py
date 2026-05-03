import os
import re
import json
from openai import OpenAI
from backend.services.ai_service import get_client

_RULES = [
    {
        "patterns": [
            r"\brigged\b", r"\bfraud\b", r"\bfake votes?\b", r"\bstolen election\b",
            r"\bvoter fraud\b", r"\belection fraud\b", r"\billegal votes?\b",
            r"\bvote tampering\b", r"\bballot stuffing\b", r"\bmanipulated\b"
        ],
        "risk_score": 85,
        "classification": "HIGH_RISK",
        "confidence": "HIGH",
        "verdict": "MISLEADING",
        "explanation": (
            "This claim contains language commonly associated with election misinformation. "
            "Allegations of widespread fraud without verified evidence are a known misinformation pattern. "
            "Please verify with your official electoral authority."
        ),
        "source_hint": "Your national electoral commission or independent fact-checkers",
    },
    {
        "patterns": [
            r"\bvoting machines?\b.*\bhack\b", r"\bhack\b.*\bvoting machines?\b",
            r"\belectronic.*tamper\b", r"\btamper.*electronic\b",
            r"\bEVM.*hack\b", r"\bhack.*EVM\b",
        ],
        "risk_score": 80,
        "classification": "HIGH_RISK",
        "confidence": "HIGH",
        "verdict": "MISLEADING",
        "explanation": (
            "Claims about voting machines being hacked are frequently circulated without credible evidence. "
            "Most certified electoral systems have multiple physical and software safeguards. "
            "Verify claims with your country's electoral authority."
        ),
        "source_hint": "Your country's electoral commission or certified cybersecurity auditors",
    },
    {
        "patterns": [
            r"\bvote.*twice\b", r"\bvote.*multiple times\b", r"\bdouble voting\b",
            r"\bimpersonat\b",
        ],
        "risk_score": 70,
        "classification": "HIGH_RISK",
        "confidence": "HIGH",
        "verdict": "MISLEADING",
        "explanation": (
            "Claims suggesting it is easy to vote multiple times misrepresent how electoral safeguards work. "
            "Voter rolls, ID verification, and ink marking prevent most forms of duplicate voting."
        ),
        "source_hint": "Your national electoral commission",
    },
    {
        "patterns": [
            r"\bage.*\b2[1-9]\b", r"\b2[1-9]\b.*\bage\b",
            r"\bneed to be.*\b2[1-9]\b", r"\bmust be.*\b2[1-9]\b",
            r"\bvoting age.*\b2[1-9]\b",
        ],
        "risk_score": 65,
        "classification": "MEDIUM_RISK",
        "confidence": "HIGH",
        "verdict": "FALSE",
        "explanation": (
            "The voting age in most democracies is 18, not higher. "
            "This claim is likely inaccurate. Always verify the specific voting age for your country "
            "with the official electoral authority."
        ),
        "source_hint": "Your country's official electoral commission website",
    },
    {
        "patterns": [
            r"\bregistration.*deadline\b", r"\bdeadline.*register\b",
            r"\blast day.*register\b", r"\bregister.*last day\b",
            r"\bregistration.*close[sd]?\b",
        ],
        "risk_score": 30,
        "classification": "LOW_RISK",
        "confidence": "MEDIUM",
        "verdict": "CONTEXT_NEEDED",
        "explanation": (
            "Registration deadlines vary by country and election cycle. "
            "This claim may be accurate or outdated. Always check with your electoral authority "
            "for the current deadline."
        ),
        "source_hint": "Your country's official electoral commission website",
    },
    {
        "patterns": [
            r"\bno id\b.*\bvote\b", r"\bvote\b.*\bno id\b",
            r"\bwithout id\b.*\bvote\b", r"\bvote\b.*\bwithout id\b",
            r"\bdon.t need id\b", r"\bno photo id\b",
        ],
        "risk_score": 45,
        "classification": "MEDIUM_RISK",
        "confidence": "MEDIUM",
        "verdict": "CONTEXT_NEEDED",
        "explanation": (
            "ID requirements for voting differ widely by country. In some countries ID is mandatory, "
            "in others it is not required. This claim needs country-specific verification."
        ),
        "source_hint": "Your country's official electoral commission",
    },
]

_SAFE_FALLBACK = {
    "success": True,
    "risk_score": 50,
    "classification": "UNVERIFIED",
    "confidence": "LOW",
    "verdict": "UNVERIFIED",
    "explanation": (
        "Unable to fully verify this claim automatically. "
        "Please check with your official electoral authority or a trusted fact-checking organisation."
    ),
    "source": "fallback",
    "color": "yellow",
}

_HINDI_LABELS = {
    "HIGH_RISK": "उच्च जोखिम",
    "MEDIUM_RISK": "मध्यम जोखिम",
    "LOW_RISK": "कम जोखिम",
    "UNVERIFIED": "असत्यापित",
    "TRUE": "सत्य",
    "FALSE": "असत्य",
    "MISLEADING": "भ्रामक",
    "CONTEXT_NEEDED": "संदर्भ आवश्यक",
}


def _color_for_score(score: int) -> str:
    if score <= 25:
        return "green"
    if score <= 45:
        return "yellow"
    if score <= 70:
        return "orange"
    return "red"


def _rule_match(claim: str) -> dict | None:
    text = claim.lower()
    for rule in _RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return rule
    return None


def _ai_explain(claim: str, country: str, language: str, rule_result: dict) -> str:
    try:
        client = get_client()
        lang_note = "Respond in Hindi." if language == "hi" else "Respond in English."
        country_note = f" Focus on {country}." if country else ""
        prompt = (
            f"Provide a concise fact-check explanation (2-3 sentences) for this election-related claim:\n\n"
            f'"{claim}"\n\n'
            f"Current assessment: {rule_result.get('classification', 'UNVERIFIED')} "
            f"(score {rule_result.get('risk_score', 50)}/100).{country_note} {lang_note}"
        )
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert election fact-checker. Give concise, neutral, "
                        "evidence-based explanations. Never invent sources."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
    except Exception:
        pass
    return rule_result.get("explanation", _SAFE_FALLBACK["explanation"])


def _ai_full_analysis(claim: str, country: str, language: str) -> dict | None:
    SYSTEM = """You are an expert fact-checker for elections. Return ONLY a JSON object:
{
  "risk_score": <integer 0-100>,
  "classification": <"LOW_RISK"|"MEDIUM_RISK"|"HIGH_RISK">,
  "explanation": <string>,
  "verdict": <"TRUE"|"FALSE"|"MISLEADING"|"UNVERIFIED"|"CONTEXT_NEEDED">,
  "source_hint": <string>
}
Return ONLY valid JSON, no markdown, no extra text."""

    try:
        client = get_client()
        lang_note = "Reply in Hindi." if language == "hi" else "Reply in English."
        country_note = f" Country context: {country}." if country else ""
        prompt = (
            f'Fact-check this election claim:{country_note}\n"{claim}"\n{lang_note}'
        )
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    return None


def detect_misinformation(claim: str, country: str = "", language: str = "en") -> dict:
    if not claim or not claim.strip():
        return {
            **_SAFE_FALLBACK,
            "explanation": "No claim provided. Please enter a statement to analyse.",
        }

    try:
        rule = _rule_match(claim)

        if rule:
            explanation = _ai_explain(claim, country, language, rule)
            result = {
                "success": True,
                "claim": claim,
                "risk_score": rule["risk_score"],
                "classification": rule["classification"],
                "confidence": rule["confidence"],
                "verdict": rule["verdict"],
                "explanation": explanation,
                "source": "rule_engine + ai_assist",
                "source_hint": rule.get("source_hint", "Your national electoral authority"),
                "color": _color_for_score(rule["risk_score"]),
            }
        else:
            ai = _ai_full_analysis(claim, country, language)
            if ai:
                score = int(ai.get("risk_score", 50))
                result = {
                    "success": True,
                    "claim": claim,
                    "risk_score": score,
                    "classification": ai.get("classification", "UNVERIFIED"),
                    "confidence": "MEDIUM",
                    "verdict": ai.get("verdict", "UNVERIFIED"),
                    "explanation": ai.get("explanation", _SAFE_FALLBACK["explanation"]),
                    "source": "ai_assist",
                    "source_hint": ai.get("source_hint", "Your national electoral authority"),
                    "color": _color_for_score(score),
                }
            else:
                result = {
                    **_SAFE_FALLBACK,
                    "claim": claim,
                    "explanation": (
                        "This claim appears to be general election information. "
                        "We could not determine a specific risk level. "
                        "Please verify with your official electoral authority."
                    ),
                }

        if language == "hi":
            result["classification"] = _HINDI_LABELS.get(
                result["classification"], result["classification"]
            )
            result["verdict"] = _HINDI_LABELS.get(result["verdict"], result["verdict"])

        return result

    except Exception:
        return {**_SAFE_FALLBACK, "claim": claim}
