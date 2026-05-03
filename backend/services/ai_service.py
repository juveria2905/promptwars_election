import os
import json
import re
from openai import OpenAI

_client = None
_country_cache = {}

COUNTRIES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'countries')

SYSTEM_PROMPT = """You are VoteIQ, an expert election information assistant. You provide accurate,
non-partisan information about elections, voting procedures, voter rights, and electoral processes
worldwide.

STRICT RULES:
1. You NEVER decide a user's eligibility — only the rule-based system does that.
2. You NEVER invent facts or speculate about specific election outcomes.
3. You provide factual, verifiable information only.
4. You are politically neutral — never favor any party, candidate, or ideology.
5. If you don't know something specific, say so clearly and direct to official sources.
6. Always encourage users to verify information with their official electoral authority.
7. Do NOT hallucinate — if uncertain, say "I recommend checking with your electoral authority."

You help with:
- Explaining voting procedures and processes
- Describing voter registration steps
- Explaining election systems (proportional representation, first-past-the-post, etc.)
- Providing general information about electoral authorities
- Answering questions about voter rights
- Explaining how elections work in different countries
"""

_KEYWORD_FALLBACKS = [
    {
        "patterns": [r"\bregister\b", r"\bregistration\b", r"\benrol\b", r"\benroll\b"],
        "field": "registration_steps",
        "intro": "Here are the voter registration steps",
    },
    {
        "patterns": [r"\bhow to vote\b", r"\bvoting steps\b", r"\bvoting process\b", r"\bcast.*ballot\b"],
        "field": "voting_steps",
        "intro": "Here is how to vote",
    },
    {
        "patterns": [r"\bid\b", r"\bdocument\b", r"\bidentif\b", r"\bproof\b"],
        "field": "approved_ids",
        "intro": "Accepted identification documents",
    },
    {
        "patterns": [r"\bage\b", r"\bminimum age\b", r"\bold enough\b", r"\bhow old\b"],
        "field": "min_age",
        "intro": "Minimum voting age",
    },
    {
        "patterns": [r"\bhours?\b", r"\btime\b", r"\bwhen.*vote\b", r"\bopen\b"],
        "field": "voting_hours",
        "intro": "Voting hours",
    },
    {
        "patterns": [r"\bauthority\b", r"\bcommission\b", r"\bofficial\b", r"\bwebsite\b"],
        "field": "authority",
        "intro": "Official electoral authority",
    },
]

_GENERIC_FALLBACKS = {
    "register": (
        "To register to vote, you generally need to: (1) Visit your national electoral commission website "
        "or office. (2) Provide proof of identity such as a national ID or passport. "
        "(3) Provide proof of address. (4) Complete the voter registration form. "
        "(5) Wait for confirmation. Always verify the exact steps with your official electoral authority."
    ),
    "vote": (
        "To vote: (1) Confirm your voter registration status. (2) Find your assigned polling station. "
        "(3) Bring valid photo ID on election day. (4) Arrive during voting hours. "
        "(5) Collect and mark your ballot privately. (6) Submit your completed ballot. "
        "Verify details with your official electoral authority."
    ),
    "age": (
        "The minimum voting age in most countries is 18 years. Some countries allow voting at 16 or 17. "
        "Please verify the specific age requirement for your country with the official electoral authority."
    ),
    "id": (
        "Most countries require a government-issued photo ID to vote, such as a national ID card, "
        "passport, or driving licence. Requirements vary — check with your electoral authority."
    ),
    "default": (
        "For accurate election information, please visit your country's official electoral commission "
        "website or contact them directly. I can answer specific questions about voting procedures, "
        "registration, voter rights, and election systems."
    ),
}


def get_client() -> OpenAI:
    global _client
    if _client is None:
        base_url = os.environ.get('AI_INTEGRATIONS_OPENAI_BASE_URL')
        api_key = os.environ.get('AI_INTEGRATIONS_OPENAI_API_KEY', 'dummy-key')
        if base_url:
            _client = OpenAI(base_url=base_url, api_key=api_key)
        else:
            _client = OpenAI(api_key=api_key)
    return _client


def _load_country_data(country: str) -> dict:
    if not country:
        return _load_fallback()
    key = country.lower().strip().replace(' ', '_')
    if key in _country_cache:
        return _country_cache[key]
    path = os.path.join(COUNTRIES_DIR, f'{key}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _country_cache[key] = data
        return data
    return _load_fallback()


def _load_fallback() -> dict:
    if '__fallback__' in _country_cache:
        return _country_cache['__fallback__']
    path = os.path.join(COUNTRIES_DIR, 'global_fallback.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _country_cache['__fallback__'] = data
    return data


def _build_country_context(country_data: dict) -> str:
    lines = []
    name = country_data.get('name', 'this country')
    lines.append(f"Country: {name}")
    if 'min_age': lines.append(f"Minimum voting age: {country_data.get('min_age', 18)}")
    if country_data.get('authority'):
        lines.append(f"Electoral authority: {country_data['authority']}")
    if country_data.get('authority_website'):
        lines.append(f"Official website: {country_data['authority_website']}")
    if country_data.get('voting_hours'):
        lines.append(f"Voting hours: {country_data['voting_hours']}")
    if country_data.get('registration_steps'):
        steps = '\n  - '.join(country_data['registration_steps'])
        lines.append(f"Registration steps:\n  - {steps}")
    if country_data.get('voting_steps'):
        steps = '\n  - '.join(country_data['voting_steps'])
        lines.append(f"Voting steps:\n  - {steps}")
    if country_data.get('approved_ids'):
        ids = ', '.join(country_data['approved_ids'])
        lines.append(f"Accepted IDs: {ids}")
    if country_data.get('notes'):
        lines.append(f"Notes: {country_data['notes']}")
    return '\n'.join(lines)


def _deterministic_fallback(message: str, country_data: dict, country: str) -> str:
    msg = message.lower()
    for rule in _KEYWORD_FALLBACKS:
        for pattern in rule["patterns"]:
            if re.search(pattern, msg, re.IGNORECASE):
                field = rule["field"]
                val = country_data.get(field)
                name = country_data.get('name', country or 'your country')
                authority = country_data.get('authority', 'your national electoral authority')
                website = country_data.get('authority_website', '')
                intro = f"{rule['intro']} for {name}:"
                if isinstance(val, list) and val:
                    steps = '\n'.join(f"{i+1}. {s}" for i, s in enumerate(val))
                    suffix = f"\n\nAlways verify with {authority}."
                    if website:
                        suffix += f" Website: {website}"
                    return f"{intro}\n\n{steps}{suffix}"
                if val:
                    suffix = f"\n\nVerify with {authority}."
                    if website:
                        suffix += f" Website: {website}"
                    return f"{intro} {val}{suffix}"

    for key, text in _GENERIC_FALLBACKS.items():
        if key != 'default' and key in msg:
            name = country_data.get('name', country or 'your country')
            authority = country_data.get('authority', 'your national electoral authority')
            return text + f"\n\n(Source: General guidance for {name}. Verify with {authority}.)"

    name = country_data.get('name', country or 'your country')
    authority = country_data.get('authority', 'your national electoral authority')
    website = country_data.get('authority_website', '')
    response = (
        f"For election information about {name}, I recommend contacting "
        f"{authority}."
    )
    if website:
        response += f" Official website: {website}"
    if country_data.get('notes'):
        response += f"\n\n{country_data['notes']}"
    return response


def chat(message: str, country: str = '', language: str = 'en', history: list = None) -> dict:
    country_data = _load_country_data(country)
    country_context = _build_country_context(country_data)
    is_fallback_data = country_data.get('fallback', False)

    lang_note = ""
    if language == 'hi':
        lang_note = " Respond in Hindi (हिंदी)."

    system = (
        SYSTEM_PROMPT
        + f"\n\nCountry data for this session:\n{country_context}"
        + f"\n\nUse the above data to answer accurately.{lang_note}"
    )

    messages = [{"role": "system", "content": system}]
    if history:
        for h in history[-6:]:
            if h.get('role') in ('user', 'assistant') and h.get('content'):
                messages.append({"role": h['role'], "content": h['content']})
    messages.append({"role": "user", "content": message})

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
        )
        reply = (response.choices[0].message.content or "").strip()
        if reply:
            source = "country_data" if not is_fallback_data else "fallback"
            return {
                "success": True,
                "response": reply,
                "source": source,
                "confidence": "HIGH" if not is_fallback_data else "MEDIUM",
            }
    except Exception:
        pass

    reply = _deterministic_fallback(message, country_data, country)
    return {
        "success": True,
        "response": reply,
        "source": "fallback",
        "confidence": "MEDIUM",
        "reason": "AI unavailable, fallback used",
    }


def explain_eligibility(eligibility_result: dict, language: str = 'en') -> dict:
    country = eligibility_result.get('country', 'the selected country')
    eligible = eligibility_result.get('eligible', False)
    reason = eligibility_result.get('reason', '')

    lang_instruction = "Respond in Hindi." if language == 'hi' else "Respond in English."
    prompt = (
        f"A voter eligibility check has been completed for {country}.\n"
        f"Result: {'ELIGIBLE' if eligible else 'NOT ELIGIBLE'}\n"
        f"Reason: {reason}\n\n"
        f"Please provide a brief, helpful explanation of what this means for the user "
        f"and what they should do next. Be encouraging and practical. Keep it to 2-3 sentences. "
        f"{lang_instruction}"
    )

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        if content:
            return {"success": True, "explanation": content}
    except Exception:
        pass

    return {"success": True, "explanation": reason}
