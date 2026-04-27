from flask import Flask, jsonify, request, session
from flask_cors import CORS
import secrets

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = secrets.token_hex(32)
CORS(app)

USERS_DB = {
    'dlozada@fqp.cl': {
        'password': 'Solera.123',
        'role': 'admin',
        'name': 'Daniela Lozada',
        'status': 'active'
    }
}

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').lower()
    password = data.get('password', '')
    
    if email not in USERS_DB:
        return jsonify({'error': 'Usuario no encontrado'}), 401
    
    user = USERS_DB[email]
    if user['password'] != password or user['status'] != 'active':
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    session['user'] = email
    session['role'] = user['role']
    
    return jsonify({
        'success': True,
        'user': {
            'email': email,
            'name': user['name'],
            'role': user['role']
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/')
def index():
    return app.send_static_file('fqp_reporteria_v2.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
