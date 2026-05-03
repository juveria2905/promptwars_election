from flask import Blueprint, request, jsonify, session
from backend.services.decision_engine import process_flow, get_flow_steps
from backend.services.eligibility_checker import list_available_countries, load_country_rules

bp = Blueprint('eligibility', __name__)

@bp.route('/api/eligibility', methods=['POST'])
def check_eligibility():
    data = request.get_json(silent=True) or {}
    answers = {
        'country': data.get('country', ''),
        'age': data.get('age', 0),
        'citizenship': data.get('citizenship', False),
        'residency': data.get('residency', False),
    }

    if not answers['country']:
        return jsonify({
            "error": "Country is required",
            "reason": "Please select a country",
            "confidence": "LOW"
        }), 400

    try:
        result = process_flow(answers)
        if session.get('username') and result.get('eligible') is not None:
            from backend.services.auth_service import update_user_progress
            update_user_progress(
                session['username'],
                result.get('progress', 60),
                result
            )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "error": "Eligibility check failed",
            "reason": str(e),
            "confidence": "LOW"
        }), 500

@bp.route('/api/flow-steps', methods=['GET'])
def flow_steps():
    return jsonify({"steps": get_flow_steps()})

@bp.route('/api/countries', methods=['GET'])
def countries():
    available = list_available_countries()
    all_countries = [
        {"name": "Afghanistan", "slug": "afghanistan"},
        {"name": "Albania", "slug": "albania"},
        {"name": "Algeria", "slug": "algeria"},
        {"name": "Argentina", "slug": "argentina"},
        {"name": "Australia", "slug": "australia"},
        {"name": "Austria", "slug": "austria"},
        {"name": "Bangladesh", "slug": "bangladesh"},
        {"name": "Belgium", "slug": "belgium"},
        {"name": "Brazil", "slug": "brazil"},
        {"name": "Canada", "slug": "canada"},
        {"name": "Chile", "slug": "chile"},
        {"name": "China", "slug": "china"},
        {"name": "Colombia", "slug": "colombia"},
        {"name": "Czech Republic", "slug": "czech_republic"},
        {"name": "Denmark", "slug": "denmark"},
        {"name": "Egypt", "slug": "egypt"},
        {"name": "Ethiopia", "slug": "ethiopia"},
        {"name": "Finland", "slug": "finland"},
        {"name": "France", "slug": "france"},
        {"name": "Germany", "slug": "germany"},
        {"name": "Ghana", "slug": "ghana"},
        {"name": "Greece", "slug": "greece"},
        {"name": "Hungary", "slug": "hungary"},
        {"name": "India", "slug": "india"},
        {"name": "Indonesia", "slug": "indonesia"},
        {"name": "Iran", "slug": "iran"},
        {"name": "Iraq", "slug": "iraq"},
        {"name": "Ireland", "slug": "ireland"},
        {"name": "Israel", "slug": "israel"},
        {"name": "Italy", "slug": "italy"},
        {"name": "Japan", "slug": "japan"},
        {"name": "Jordan", "slug": "jordan"},
        {"name": "Kenya", "slug": "kenya"},
        {"name": "Malaysia", "slug": "malaysia"},
        {"name": "Mexico", "slug": "mexico"},
        {"name": "Morocco", "slug": "morocco"},
        {"name": "Netherlands", "slug": "netherlands"},
        {"name": "New Zealand", "slug": "new_zealand"},
        {"name": "Nigeria", "slug": "nigeria"},
        {"name": "Norway", "slug": "norway"},
        {"name": "Pakistan", "slug": "pakistan"},
        {"name": "Peru", "slug": "peru"},
        {"name": "Philippines", "slug": "philippines"},
        {"name": "Poland", "slug": "poland"},
        {"name": "Portugal", "slug": "portugal"},
        {"name": "Romania", "slug": "romania"},
        {"name": "Russia", "slug": "russia"},
        {"name": "Saudi Arabia", "slug": "saudi_arabia"},
        {"name": "South Africa", "slug": "south_africa"},
        {"name": "South Korea", "slug": "south_korea"},
        {"name": "Spain", "slug": "spain"},
        {"name": "Sweden", "slug": "sweden"},
        {"name": "Switzerland", "slug": "switzerland"},
        {"name": "Thailand", "slug": "thailand"},
        {"name": "Turkey", "slug": "turkey"},
        {"name": "Ukraine", "slug": "ukraine"},
        {"name": "United Kingdom", "slug": "uk"},
        {"name": "United States", "slug": "usa"},
        {"name": "Venezuela", "slug": "venezuela"},
        {"name": "Vietnam", "slug": "vietnam"},
    ]
    available_slugs = {c['slug'] for c in available}
    for c in all_countries:
        c['has_data'] = c['slug'] in available_slugs
    return jsonify({"countries": all_countries})

@bp.route('/api/country-info', methods=['GET'])
def country_info():
    country = request.args.get('country', '')
    if not country:
        return jsonify({"error": "Country parameter required"}), 400
    rules = load_country_rules(country)
    safe_rules = {k: v for k, v in rules.items() if not k.startswith('_')}
    return jsonify(safe_rules)
