from backend.services.eligibility_checker import check_eligibility, load_country_rules

FLOW_STEPS = [
    {
        "id": "country",
        "question": "Which country are you trying to vote in?",
        "type": "country_select",
        "required": True
    },
    {
        "id": "age",
        "question": "How old are you?",
        "type": "number",
        "min": 1,
        "max": 120,
        "required": True
    },
    {
        "id": "citizenship",
        "question": "Are you a citizen of that country?",
        "type": "boolean",
        "required": True
    },
    {
        "id": "residency",
        "question": "Are you currently residing in that country?",
        "type": "boolean",
        "required": True
    }
]

def get_flow_steps() -> list:
    return FLOW_STEPS

def process_flow(answers: dict) -> dict:
    country = answers.get('country', '')
    age_raw = answers.get('age', 0)
    is_citizen = answers.get('citizenship', False)
    is_resident = answers.get('residency', False)

    try:
        age = int(age_raw)
    except (ValueError, TypeError):
        return {
            "error": "Invalid age provided",
            "reason": "Age must be a valid number",
            "confidence": "LOW"
        }

    if not country:
        return {
            "error": "Country is required",
            "reason": "Please specify a country to check eligibility",
            "confidence": "LOW"
        }

    if isinstance(is_citizen, str):
        is_citizen = is_citizen.lower() in ('true', 'yes', '1')
    if isinstance(is_resident, str):
        is_resident = is_resident.lower() in ('true', 'yes', '1')

    result = check_eligibility(age, is_citizen, is_resident, country)

    rules = load_country_rules(country)
    steps_completed = 4
    total_steps = 4
    result['steps_completed'] = steps_completed
    result['total_steps'] = total_steps

    if result['eligible']:
        result['action_items'] = build_action_items(rules, is_citizen, is_resident)
    else:
        result['action_items'] = []

    return result

def build_action_items(rules: dict, is_citizen: bool, is_resident: bool) -> list:
    items = []
    if rules.get('registration_required', True):
        items.append({
            "priority": 1,
            "action": "Register to Vote",
            "description": f"Visit {rules.get('authority', 'your national electoral authority')} to register",
            "url": rules.get('authority_website', '')
        })
    items.append({
        "priority": 2,
        "action": "Find Your Polling Station",
        "description": "Locate your assigned polling place before election day"
    })
    if rules.get('id_required', False):
        items.append({
            "priority": 3,
            "action": "Prepare Your ID",
            "description": "Bring a valid photo ID to the polling station"
        })
    items.append({
        "priority": 4,
        "action": "Check Election Dates",
        "description": "Know when the next election is in your country"
    })
    return items
