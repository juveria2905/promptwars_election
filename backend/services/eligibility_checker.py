import json
import os
import re

COUNTRIES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'countries')

_country_cache = {}

def normalize_country_name(country: str) -> str:
    country = country.lower().strip()
    country = re.sub(r'\bin\b', '', country).strip()
    country = re.sub(r'[^a-z\s]', '', country).strip()
    country = re.sub(r'\s+', '_', country)
    aliases = {
        'united_states': 'usa',
        'united_states_of_america': 'usa',
        'us': 'usa',
        'america': 'usa',
        'united_kingdom': 'uk',
        'great_britain': 'uk',
        'britain': 'uk',
        'england': 'uk',
        'india': 'india',
        'bharat': 'india',
        'deutschland': 'germany',
        'bundesrepublik_deutschland': 'germany',
        'oz': 'australia',
        'au': 'australia',
        'canada': 'canada',
        'ca': 'canada',
        'de': 'germany',
        'gb': 'uk',
        'in': 'india',
    }
    return aliases.get(country, country)

def load_country_rules(country: str) -> dict:
    normalized = normalize_country_name(country)
    if normalized in _country_cache:
        return _country_cache[normalized]

    path = os.path.join(COUNTRIES_DIR, f'{normalized}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['_found'] = True
        _country_cache[normalized] = data
        return data

    fallback_path = os.path.join(COUNTRIES_DIR, 'global_fallback.json')
    with open(fallback_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['_found'] = False
    data['_queried'] = country
    _country_cache[normalized] = data
    return data

def check_eligibility(age: int, is_citizen: bool, is_resident: bool, country: str) -> dict:
    rules = load_country_rules(country)
    country_name = rules.get('name', country.title())
    min_age = rules.get('min_age', 18)
    citizenship_required = rules.get('citizenship_required', True)
    residency_required = rules.get('residency_required', True)
    is_fallback = not rules.get('_found', True)

    reasons = []
    eligible = True

    if age < min_age:
        eligible = False
        reasons.append(f"You must be at least {min_age} years old to vote in {country_name}. You are {age}.")

    if citizenship_required and not is_citizen:
        eligible = False
        reasons.append(f"Citizenship is required to vote in {country_name}.")
    elif not citizenship_required and not is_citizen:
        reasons.append(f"Note: Some non-citizens may be eligible to vote in {country_name} under specific conditions.")

    if residency_required and not is_resident:
        eligible = False
        reasons.append(f"You must be a current resident of {country_name} to vote.")

    if eligible:
        reason = f"You meet the basic eligibility requirements to vote in {country_name}."
        if min_age <= age < min_age + 2:
            reason += f" You just became eligible — welcome to voting!"
        confidence = "HIGH" if rules.get('_found', True) else "MEDIUM"
        next_step = "Check your voter registration status and find your polling station."
        if rules.get('registration_required', True):
            next_step = "Register to vote as soon as possible to participate in upcoming elections."
        progress = 60
    else:
        reason = " ".join(reasons)
        confidence = "HIGH" if rules.get('_found', True) else "MEDIUM"
        next_step = "Review the eligibility requirements and check again when your situation changes."
        progress = 20

    result = {
        "eligible": eligible,
        "country": country_name,
        "reason": reason,
        "confidence": confidence if not is_fallback else "MEDIUM",
        "progress": progress,
        "next_step": next_step,
        "min_age": min_age,
        "citizenship_required": citizenship_required,
        "residency_required": residency_required,
    }

    if is_fallback:
        result["notice"] = "Specific country data not available. Showing general election guidance."

    return result

def list_available_countries() -> list:
    countries = []
    for filename in os.listdir(COUNTRIES_DIR):
        if filename.endswith('.json') and filename != 'global_fallback.json':
            name = filename.replace('.json', '').replace('_', ' ').title()
            slug = filename.replace('.json', '')
            countries.append({"name": name, "slug": slug})
    return sorted(countries, key=lambda x: x['name'])
