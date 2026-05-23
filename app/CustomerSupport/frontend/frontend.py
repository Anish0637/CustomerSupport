import json
import os
import re
import uuid
import base64
from pathlib import Path
from urllib.parse import urlencode, quote

import requests
from flask import Flask, redirect, render_template, request, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'agentcore-workshop-dev-secret')

REGION = 'us-east-1'
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID', '4hqbuvfji23kgdeqqn2cujs5p4')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'http://localhost:8501/callback')
COGNITO_DOMAIN = os.environ.get(
    'COGNITO_DOMAIN',
    'https://customersupport-workshop.auth.us-east-1.amazoncognito.com',
)

_runtime_arn: str | None = None


def get_runtime_arn() -> str:
    global _runtime_arn
    if _runtime_arn:
        return _runtime_arn
    # frontend/ -> CustomerSupport/ -> app/ -> CustomerSupport (repo root)
    state_path = (
        Path(__file__).parent   # frontend/
        .parent                 # app/CustomerSupport/
        .parent                 # app/
        .parent                 # CustomerSupport/ (repo root)
        / 'agentcore' / '.cli' / 'deployed-state.json'
    )
    with open(state_path) as f:
        state = json.load(f)
    _runtime_arn = (
        state['targets']['default']['resources']['runtimes']['CustomerSupport']['runtimeArn']
    )
    return _runtime_arn


def get_invoke_url(runtime_arn: str) -> str:
    return (
        f"https://bedrock-agentcore.{REGION}.amazonaws.com"
        f"/runtimes/{quote(runtime_arn, safe='')}/invocations"
    )


@app.route('/')
def index():
    if 'token' not in session:
        login_url = COGNITO_DOMAIN + '/oauth2/authorize?' + urlencode({
            'client_id': COGNITO_CLIENT_ID,
            'response_type': 'code',
            'scope': 'openid email profile',
            'redirect_uri': REDIRECT_URI,
        })
        return render_template('login.html', login_url=login_url)
    return render_template(
        'index.html',
        runtime_arn=get_runtime_arn(),
        username=session.get('username', 'User'),
    )


@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return redirect('/')
    resp = requests.post(
        COGNITO_DOMAIN + '/oauth2/token',
        data={
            'grant_type': 'authorization_code',
            'client_id': COGNITO_CLIENT_ID,
            'code': code,
            'redirect_uri': REDIRECT_URI,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=15,
    )
    resp.raise_for_status()
    tokens = resp.json()
    access_token = tokens.get('access_token', '')
    session['token'] = access_token

    # Decode username from JWT payload (signature already validated by Cognito)
    try:
        payload = access_token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        session['username'] = claims.get('username') or claims.get('email') or 'User'
    except Exception:
        session['username'] = 'User'

    session['session_id'] = str(uuid.uuid4())
    return redirect('/')


@app.route('/chat', methods=['POST'])
def chat():
    if 'token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json or {}
    prompt = data.get('prompt', '')
    session_id = data.get('session_id') or session.get('session_id') or str(uuid.uuid4())
    runtime_arn = get_runtime_arn()
    invoke_url = get_invoke_url(runtime_arn)

    try:
        resp = requests.post(
            invoke_url,
            json={'prompt': prompt},
            headers={
                'Authorization': f"Bearer {session['token']}",
                'Content-Type': 'application/json',
                'X-Amzn-Bedrock-AgentCore-Session-Id': session_id,
            },
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()

        # Parse SSE streaming response: each line is: data: "<json-string>"
        full_text = ''
        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode('utf-8') if isinstance(line, bytes) else line
            if decoded.startswith('data: '):
                raw = decoded[6:]
                try:
                    chunk = json.loads(raw)
                except Exception:
                    chunk = raw.strip('"')
                full_text += chunk

        # Strip model <thinking>...</thinking> reasoning blocks
        response = re.sub(r'<thinking>.*?</thinking>\s*', '', full_text, flags=re.DOTALL).strip()
        return jsonify({'response': response})

    except requests.exceptions.HTTPError as e:
        return jsonify({'error': f'AgentCore {e.response.status_code}: {e.response.text[:300]}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logout')
def logout():
    session.clear()
    logout_url = COGNITO_DOMAIN + '/logout?' + urlencode({
        'client_id': COGNITO_CLIENT_ID,
        'logout_uri': 'http://localhost:8501/',
    })
    return redirect(logout_url)


if __name__ == '__main__':
    arn = get_runtime_arn()
    print(f"Runtime ARN: {arn}")
    print(f"Invoke URL:  {get_invoke_url(arn)}")
    app.run(host='0.0.0.0', port=8501, debug=True)
