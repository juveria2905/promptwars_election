from flask import Blueprint, request, jsonify, session
from backend.services.auth_service import signup, login, verify_token, get_user

bp = Blueprint('auth', __name__)

def get_current_user():
    token = request.cookies.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        return verify_token(token)
    if session.get('username'):
        return {'username': session['username'], 'country': session.get('country', ''), 'language': session.get('language', 'en')}
    return None

@bp.route('/api/signup', methods=['POST'])
def signup_endpoint():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    country = data.get('country', '')
    language = data.get('language', 'en')

    result = signup(username, password, country, language)
    if result['success']:
        session['username'] = result['username']
        session['country'] = result.get('country', '')
        session['language'] = result.get('language', 'en')
        response = jsonify(result)
        response.set_cookie('token', result['token'], httponly=True, max_age=86400 * 7, samesite='Lax')
        return response
    return jsonify(result), 400

@bp.route('/api/login', methods=['POST'])
def login_endpoint():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    result = login(username, password)
    if result['success']:
        session['username'] = result['username']
        session['country'] = result.get('country', '')
        session['language'] = result.get('language', 'en')
        response = jsonify(result)
        response.set_cookie('token', result['token'], httponly=True, max_age=86400 * 7, samesite='Lax')
        return response
    return jsonify(result), 401

@bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    response = jsonify({"success": True})
    response.delete_cookie('token')
    return response

@bp.route('/api/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 401
    user_data = get_user(user.get('username', ''))
    if user_data:
        return jsonify({
            "authenticated": True,
            "username": user_data['username'],
            "country": user_data.get('country', ''),
            "language": user_data.get('language', 'en'),
            "progress": user_data.get('progress', 0),
            "eligibility": user_data.get('eligibility')
        })
    return jsonify({"authenticated": True, "username": user.get('username'), "country": user.get('country', ''), "language": user.get('language', 'en'), "progress": 0})
