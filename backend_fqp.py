"""
FQP Reportería - Backend Flask
Conecta a Snowflake, maneja autenticación y expone APIs para dashboards
"""

from flask import Flask, jsonify, request, session
from flask_cors import CORS
import snowflake.connector
import json
from datetime import datetime, timedelta
import os
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Configuración Snowflake
SNOWFLAKE_CONFIG = {
    'user': 'BACKEND_READONLY',
    'password': 'Backend@Render2026',
    'account': 'ru11436.us-east-2.aws',
    'warehouse': 'COMPUTE_WH',
    'database': 'COMERCIAL',
    'schema': 'DANIELA'
}

# Base de datos de usuarios (en producción usar Snowflake)
USERS_DB = {
    'dlozada@fqp.cl': {
        'password': 'Solera.123',
        'role': 'admin',
        'name': 'Daniela Lozada',
        'status': 'active'
    }
}

ROLES_PERMISSIONS = {
    'admin': ['view_all', 'manage_users', 'export_data'],
    'gerente': ['view_all', 'export_data'],
    'ejecutivo': ['view_summary']
}

# ═══════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════

def get_snowflake_conn():
    """Conecta a Snowflake"""
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        return conn
    except Exception as e:
        print(f"Error conectando Snowflake: {e}")
        return None

def require_login(f):
    """Decorator para rutas que requieren login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_role(*roles):
    """Decorator para verificar roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return jsonify({'error': 'No autenticado'}), 401
            
            user_role = USERS_DB[session['user']].get('role')
            if user_role not in roles:
                return jsonify({'error': 'Permisos insuficientes'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ═══════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login de usuarios"""
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
    """Logout"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/current', methods=['GET'])
def get_current_user():
    """Obtiene usuario actual"""
    if 'user' not in session:
        return jsonify({'user': None})
    
    email = session['user']
    user = USERS_DB[email]
    return jsonify({
        'user': {
            'email': email,
            'name': user['name'],
            'role': user['role']
        }
    })

# ═══════════════════════════════════════════════════════════════
# GESTIÓN DE USUARIOS (ADMIN ONLY)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/admin/users', methods=['GET'])
@require_login
@require_role('admin')
def get_users():
    """Lista todos los usuarios"""
    users = []
    for email, data in USERS_DB.items():
        users.append({
            'email': email,
            'name': data['name'],
            'role': data['role'],
            'status': data['status'],
            'permissions': ROLES_PERMISSIONS.get(data['role'], [])
        })
    return jsonify({'users': users})

@app.route('/api/admin/users', methods=['POST'])
@require_login
@require_role('admin')
def create_user():
    """Crea nuevo usuario"""
    data = request.json
    email = data.get('email', '').lower()
    
    if email in USERS_DB:
        return jsonify({'error': 'El usuario ya existe'}), 400
    
    if not data.get('password') or len(data['password']) < 8:
        return jsonify({'error': 'Contraseña debe tener al menos 8 caracteres'}), 400
    
    role = data.get('role', 'ejecutivo')
    if role not in ROLES_PERMISSIONS:
        return jsonify({'error': 'Rol inválido'}), 400
    
    USERS_DB[email] = {
        'password': data['password'],
        'role': role,
        'name': data.get('name', email),
        'status': 'active'
    }
    
    return jsonify({
        'success': True,
        'user': {
            'email': email,
            'name': USERS_DB[email]['name'],
            'role': role,
            'permissions': ROLES_PERMISSIONS[role]
        }
    })

@app.route('/api/admin/users/<email>', methods=['PUT'])
@require_login
@require_role('admin')
def update_user(email):
    """Actualiza usuario"""
    email = email.lower()
    
    if email not in USERS_DB:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    data = request.json
    user = USERS_DB[email]
    
    if 'name' in data:
        user['name'] = data['name']
    if 'role' in data and data['role'] in ROLES_PERMISSIONS:
        user['role'] = data['role']
    if 'status' in data:
        user['status'] = data['status']
    if 'password' in data and len(data['password']) >= 8:
        user['password'] = data['password']
    
    return jsonify({
        'success': True,
        'user': {
            'email': email,
            'name': user['name'],
            'role': user['role'],
            'status': user['status']
        }
    })

@app.route('/api/admin/users/<email>', methods=['DELETE'])
@require_login
@require_role('admin')
def delete_user(email):
    """Desactiva usuario (soft delete)"""
    email = email.lower()
    
    if email not in USERS_DB:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    if email == session.get('user'):
        return jsonify({'error': 'No puedes eliminar tu propia cuenta'}), 400
    
    USERS_DB[email]['status'] = 'inactive'
    
    return jsonify({'success': True})

# ═══════════════════════════════════════════════════════════════
# DATOS - KPIs
# ═══════════════════════════════════════════════════════════════

@app.route('/api/kpis/resumen', methods=['GET'])
@require_login
def get_resumen_kpis():
    """Resumen ejecutivo - lecturas de Snowflake"""
    conn = get_snowflake_conn()
    if not conn:
        return jsonify({'error': 'Error conectando a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Ventas actuales vs presupuesto
        query_ventas = """
        SELECT 
            COALESCE(SUM(UNIDADES), 0) as unidades_reales,
            COALESCE(SUM(VALORES), 0) as valores_reales,
            COUNT(DISTINCT MARCA_FQP) as productos
        FROM DDD_BRICK
        WHERE FECHA_DDD >= CURRENT_DATE - 30
        """
        
        cursor.execute(query_ventas)
        ventas_data = cursor.fetchone()
        
        # Meta de presupuesto
        query_meta = """
        SELECT 
            SUM(Unidades) as unidades_meta
        FROM PPTO_SELLOUT
        WHERE FECHA >= CURRENT_DATE - 30
        """
        
        cursor.execute(query_meta)
        meta_data = cursor.fetchone()
        
        unidades_reales = float(ventas_data[0]) if ventas_data[0] else 0
        unidades_meta = float(meta_data[0]) if meta_data[0] else 1
        cumplimiento = (unidades_reales / unidades_meta * 100) if unidades_meta > 0 else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'cumplimiento_ventas': round(cumplimiento, 1),
            'unidades_reales': int(unidades_reales),
            'unidades_meta': int(unidades_meta),
            'valores_reales': float(ventas_data[1]) if ventas_data[1] else 0,
            'productos_activos': int(ventas_data[2]) if ventas_data[2] else 0
        })
    
    except Exception as e:
        print(f"Error en query: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/kpis/detalle', methods=['GET'])
@require_login
def get_kpis_detalle():
    """KPIs detallados por categoría"""
    conn = get_snowflake_conn()
    if not conn:
        return jsonify({'error': 'Error conectando a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        # KPIs por marca
        query = """
        SELECT 
            MARCA_FQP,
            SUM(UNIDADES) as unidades,
            SUM(VALORES) as valores,
            COUNT(DISTINCT BRICK_DESCRIPTOR) as puntos_venta
        FROM DDD_BRICK
        WHERE FECHA_DDD >= CURRENT_DATE - 30
        GROUP BY MARCA_FQP
        ORDER BY unidades DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        kpis = []
        for row in rows:
            kpis.append({
                'marca': row[0],
                'unidades': int(row[1]) if row[1] else 0,
                'valores': float(row[2]) if row[2] else 0,
                'puntos_venta': int(row[3]) if row[3] else 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'kpis': kpis})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/kpis/territorial', methods=['GET'])
@require_login
def get_kpis_territorial():
    """KPIs por territorio"""
    conn = get_snowflake_conn()
    if not conn:
        return jsonify({'error': 'Error conectando a base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        
        query = """
        SELECT 
            TERRITORIOS,
            SUM(META_UNIDADES) as meta,
            ROUND(SUM(META_MS_TERRITORIO), 2) as market_share_meta
        FROM META_MS_TERRITORIO
        WHERE AÑO = 2026
        GROUP BY TERRITORIOS
        ORDER BY meta DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        territorios = []
        for row in rows:
            territorios.append({
                'territorio': row[0],
                'meta_unidades': int(row[1]) if row[1] else 0,
                'meta_market_share': float(row[2]) if row[2] else 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'territorios': territorios})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════════════════════
# SALUD DEL SERVIDOR
# ═══════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    """Verifica estado del servidor"""
    conn = get_snowflake_conn()
    if conn:
        conn.close()
        return jsonify({'status': 'ok', 'snowflake': 'connected'})
    return jsonify({'status': 'error', 'snowflake': 'disconnected'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
