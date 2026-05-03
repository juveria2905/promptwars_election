from flask import Blueprint, request, jsonify
from backend.services.eligibility_checker import load_country_rules

bp = Blueprint('voting_guide', __name__)

@bp.route('/api/voting-guide', methods=['GET'])
def voting_guide():
    country = request.args.get('country', '')
    if not country:
        return jsonify({
            "error": "Country parameter required",
            "reason": "Please provide a country name",
            "confidence": "LOW"
        }), 400

    rules = load_country_rules(country)
    is_fallback = not rules.get('_found', True)

    guide = {
        "country": rules.get('name', country.title()),
        "authority": rules.get('authority', 'National Electoral Commission'),
        "authority_website": rules.get('authority_website', ''),
        "voting_hours": rules.get('voting_hours', 'Check with your local electoral authority'),
        "id_required": rules.get('id_required', False),
        "approved_ids": rules.get('approved_ids', []),
        "registration_required": rules.get('registration_required', True),
        "registration_steps": rules.get('registration_steps', []),
        "voting_steps": rules.get('voting_steps', []),
        "notes": rules.get('notes', ''),
        "compulsory_voting": rules.get('compulsory_voting', False),
        "postal_voting": rules.get('postal_voting', rules.get('postal_ballot', False)),
        "online_voting": rules.get('online_voting', False),
        "diaspora_voting": rules.get('diaspora_voting', False),
        "min_age": rules.get('min_age', 18),
        "is_fallback": is_fallback
    }

    if is_fallback:
        guide["notice"] = "Specific country data not available. Showing general election guidance. Please verify with your national electoral authority."

    return jsonify(guide)
