import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, session, redirect, url_for, request
from flask_cors import CORS

from backend.routes.eligibility import bp as eligibility_bp
from backend.routes.voting_guide import bp as voting_guide_bp
from backend.routes.chat import bp as chat_bp
from backend.routes.auth import bp as auth_bp

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)
app.secret_key = os.environ.get('SESSION_SECRET', 'voteiq-dev-secret-key')
CORS(app, supports_credentials=True)

app.register_blueprint(eligibility_bp)
app.register_blueprint(voting_guide_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(auth_bp)

def get_language():
    return session.get('language', request.args.get('lang', 'en'))

def get_country():
    return session.get('country', '')

@app.context_processor
def inject_globals():
    from backend.services.translation_service import get_all_translations
    lang = get_language()
    t = get_all_translations(lang)
    return {
        't': t,
        'lang': lang,
        'session_country': get_country(),
        'username': session.get('username', ''),
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/eligibility')
def eligibility():
    return render_template('eligibility.html')

@app.route('/voting-guide')
def voting_guide():
    return render_template('voting_guide.html')

@app.route('/fact-checker')
def fact_checker():
    return render_template('fact_checker.html')

@app.route('/assistant')
def assistant():
    return render_template('assistant.html')

@app.route('/login')
def login_page():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    if session.get('username'):
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return {'error': 'Internal server error', 'reason': str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
