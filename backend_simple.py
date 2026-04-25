from flask import Flask, jsonify, request, session
from flask_cors import CORS
import secrets
from datetime import datetime

app = Flask(__name__)
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

@app.route('/api/kpis/resumen', methods=['GET'])
def get_resumen():
    return jsonify({
        'cumplimiento_ventas': 103,
        'unidades_reales': 4750,
        'unidades_meta': 4750,
        'valores_reales': 19200000,
        'productos_activos': 8
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
