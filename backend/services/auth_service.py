import jwt
import os
import hashlib
import json
import time
from pathlib import Path

SECRET_KEY = os.environ.get('SESSION_SECRET', 'voteiq-secret-key-change-in-production')
TOKEN_EXPIRY = 86400 * 7

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')

def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def _save_users(users: dict):
    Path(USERS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username: str, password: str, country: str = '', language: str = 'en') -> dict:
    if not username or not password:
        return {"success": False, "error": "Username and password are required"}
    if len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters"}
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}

    users = _load_users()
    if username.lower() in users:
        return {"success": False, "error": "Username already exists"}

    users[username.lower()] = {
        "username": username,
        "password": _hash_password(password),
        "country": country,
        "language": language,
        "eligibility": None,
        "progress": 0,
        "created_at": int(time.time())
    }
    _save_users(users)

    token = generate_token(username, country, language)
    return {"success": True, "token": token, "username": username, "country": country, "language": language}

def login(username: str, password: str) -> dict:
    if not username or not password:
        return {"success": False, "error": "Username and password are required"}

    users = _load_users()
    user = users.get(username.lower())
    if not user:
        return {"success": False, "error": "Invalid username or password"}

    if user['password'] != _hash_password(password):
        return {"success": False, "error": "Invalid username or password"}

    token = generate_token(user['username'], user.get('country', ''), user.get('language', 'en'))
    return {
        "success": True,
        "token": token,
        "username": user['username'],
        "country": user.get('country', ''),
        "language": user.get('language', 'en'),
        "progress": user.get('progress', 0)
    }

def generate_token(username: str, country: str = '', language: str = 'en') -> str:
    payload = {
        "username": username,
        "country": country,
        "language": language,
        "exp": int(time.time()) + TOKEN_EXPIRY,
        "iat": int(time.time())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def update_user_progress(username: str, progress: int, eligibility: dict = None):
    users = _load_users()
    user = users.get(username.lower())
    if user:
        user['progress'] = progress
        if eligibility:
            user['eligibility'] = eligibility
        _save_users(users)

def get_user(username: str) -> dict | None:
    users = _load_users()
    return users.get(username.lower())
