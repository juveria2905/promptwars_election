from flask import Blueprint, request, jsonify, session
from backend.services.ai_service import chat
from backend.services.misinformation_detector import detect_misinformation
from backend.services.translation_service import get_all_translations

bp = Blueprint('chat', __name__)


def _get_param(data: dict, *keys, fallback=''):
    for k in keys:
        v = data.get(k, '').strip() if isinstance(data.get(k), str) else ''
        if v:
            return v
    return fallback


@bp.route('/api/chat', methods=['POST'])
def chat_endpoint():
    data = request.get_json(silent=True) or {}
    message = _get_param(data, 'message', 'query')
    country = data.get('country', session.get('country', ''))
    language = data.get('language', session.get('language', 'en'))
    history = data.get('history', [])

    if not message:
        return jsonify({"error": "Message is required", "confidence": "LOW"}), 400

    result = chat(message, country, language, history)
    return jsonify(result)


@bp.route('/api/assistant', methods=['POST'])
def assistant_endpoint():
    data = request.get_json(silent=True) or {}
    message = _get_param(data, 'query', 'message')
    country = data.get('country', session.get('country', ''))
    language = data.get('language', session.get('language', 'en'))
    history = data.get('history', [])

    if not message:
        return jsonify({"error": "Query is required", "confidence": "LOW"}), 400

    result = chat(message, country, language, history)
    return jsonify({
        "answer": result.get("response", ""),
        "source": result.get("source", "fallback"),
        "confidence": result.get("confidence", "MEDIUM"),
        "reason": result.get("reason", ""),
        "success": result.get("success", True),
    })


@bp.route('/api/fact-check', methods=['POST'])
def fact_check():
    data = request.get_json(silent=True) or {}
    claim = _get_param(data, 'claim', 'query')
    country = data.get('country', session.get('country', ''))
    language = data.get('language', session.get('language', 'en'))

    if not claim:
        return jsonify({"error": "Claim is required", "confidence": "LOW"}), 400

    result = detect_misinformation(claim, country, language)
    return jsonify(result)


@bp.route('/api/translations', methods=['GET'])
def translations():
    language = request.args.get('lang', session.get('language', 'en'))
    t = get_all_translations(language)
    return jsonify(t)


@bp.route('/api/set-language', methods=['POST'])
def set_language():
    data = request.get_json(silent=True) or {}
    language = data.get('language', 'en')
    if language not in ('en', 'hi'):
        return jsonify({"error": "Unsupported language"}), 400
    session['language'] = language
    return jsonify({"success": True, "language": language})
