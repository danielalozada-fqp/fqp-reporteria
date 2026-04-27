from flask import Flask, jsonify, request, session
from flask_cors import CORS
import secrets

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

# RUTAS API
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

# SERVIR HTML
@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FQP — Centro de Reportería</title>
<link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&family=Merriweather:wght@300;400&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --azul: #003F7D;
  --azul-med: #0057AA;
  --azul-claro: #E8F0F9;
  --gris-bg: #F4F6F9;
  --gris-borde: #DDE3EC;
  --texto: #1A2535;
  --muted: #6B7A94;
  --blanco: #FFFFFF;
  --font: 'Lato', sans-serif;
}
body {
  font-family: var(--font);
  background: var(--gris-bg);
  color: var(--texto);
}
#login-screen { min-height: 100vh; display: flex; align-items: stretch; }
.login-left { width: 420px; background: var(--azul); display: flex; flex-direction: column; justify-content: center; padding: 60px 48px; }
.login-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 48px; }
.login-logo-mark { width: 44px; height: 44px; background: var(--blanco); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: var(--azul); }
.login-logo-text { color: white; font-size: 13px; font-weight: 300; letter-spacing: 0.1em; text-transform: uppercase; }
.login-tagline { color: rgba(255,255,255,0.9); font-size: 22px; font-weight: 300; margin-bottom: 16px; }
.login-sub { color: rgba(255,255,255,0.5); font-size: 13px; }
.login-right { flex: 1; display: flex; align-items: center; justify-content: center; background: var(--blanco); padding: 40px; }
.login-box { width: 100%; max-width: 360px; }
.login-title { font-size: 22px; font-weight: 700; margin-bottom: 6px; }
.login-hint { font-size: 13px; color: var(--muted); margin-bottom: 36px; }
.form-group { margin-bottom: 18px; }
.form-label { display: block; font-size: 12px; font-weight: 700; text-transform: uppercase; color: var(--muted); margin-bottom: 7px; }
.form-input { width: 100%; padding: 11px 14px; border: 1.5px solid var(--gris-borde); border-radius: 8px; font-family: var(--font); font-size: 14px; color: var(--texto); outline: none; }
.form-input:focus { border-color: var(--azul-med); }
.btn-login { width: 100%; padding: 13px; background: var(--azul); color: white; border: none; border-radius: 8px; font-family: var(--font); font-size: 14px; font-weight: 700; cursor: pointer; margin-top: 8px; }
.btn-login:hover { background: var(--azul-med); }
.login-error { background: #FDF0EE; border: 1px solid #e8b4b4; border-radius: 8px; padding: 10px 14px; color: #B83232; margin-bottom: 16px; display: none; font-size: 12px; }
#app { display: none; min-height: 100vh; flex-direction: column; }
.topbar { height: 56px; background: var(--azul); display: flex; align-items: center; padding: 0 28px; gap: 20px; }
.topbar-logo { display: flex; align-items: center; gap: 10px; text-decoration: none; }
.topbar-mark { width: 32px; height: 32px; background: white; border-radius: 7px; display: flex; align-items: center; font-weight: 900; font-size: 12px; color: var(--azul); }
.topbar-name { color: rgba(255,255,255,0.9); font-size: 13px; font-weight: 700; }
.topbar-right { margin-left: auto; display: flex; gap: 16px; }
.user-info { text-align: right; }
.user-name { font-size: 12px; font-weight: 700; color: white; }
.user-role { font-size: 10px; color: rgba(255,255,255,0.5); text-transform: uppercase; }
.btn-logout { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15); color: rgba(255,255,255,0.7); padding: 5px 12px; border-radius: 6px; font-size: 11px; cursor: pointer; font-family: var(--font); }
.btn-logout:hover { background: rgba(255,255,255,0.18); }
.app-body { display: flex; flex: 1; }
.main-content { flex: 1; padding: 32px 36px; overflow-y: auto; }
.page { display: none; }
.page.active { display: block; }
.page-header { margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--gris-borde); }
.page-title { font-size: 20px; font-weight: 900; color: var(--azul); }
.page-sub { font-size: 13px; color: var(--muted); margin-top: 4px; }
</style>
</head>
<body>

<div id="login-screen">
  <div class="login-left">
    <div class="login-logo">
      <div class="login-logo-mark">FQP</div>
      <div class="login-logo-text">Farmoquímica<br>del Pacífico</div>
    </div>
    <div class="login-tagline">Centro de Reportería<br>Comercial y Estratégica</div>
    <div class="login-sub">Acceso a datos en tiempo real desde Snowflake</div>
  </div>

  <div class="login-right">
    <div class="login-box">
      <div class="login-title">Iniciar sesión</div>
      <div class="login-hint">Ingresa tus credenciales</div>

      <div class="login-error" id="login-error">Usuario o contraseña incorrectos.</div>

      <div class="form-group">
        <label class="form-label">Email</label>
        <input class="form-input" type="email" id="input-email" placeholder="usuario@fqp.cl">
      </div>
      <div class="form-group">
        <label class="form-label">Contraseña</label>
        <input class="form-input" type="password" id="input-pass" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()">
      </div>
      <button class="btn-login" onclick="doLogin()">Ingresar</button>
    </div>
  </div>
</div>

<div id="app">
  <div class="topbar">
    <div class="topbar-logo">
      <div class="topbar-mark">FQP</div>
      <span class="topbar-name">REPORTERÍA</span>
    </div>
    <div class="topbar-right">
      <div class="user-info">
        <div class="user-name" id="topbar-username">—</div>
        <div class="user-role" id="topbar-role">—</div>
      </div>
      <button class="btn-logout" onclick="doLogout()">Salir</button>
    </div>
  </div>

  <div class="app-body">
    <main class="main-content">
      <div id="p-home" class="page active">
        <div class="page-header">
          <div class="page-title">Bienvenido, <span id="welcome-name">—</span></div>
          <div class="page-sub">Centro de Reportería FQP</div>
        </div>
        <p>✓ Sistema activo en Azure</p>
        <p>✓ Backend Python Flask corriendo</p>
        <p>✓ Listo para conectar Snowflake</p>
      </div>
    </main>
  </div>
</div>

<script>
function doLogin() {
  const email = document.getElementById('input-email').value.toLowerCase();
  const password = document.getElementById('input-pass').value;
  const err = document.getElementById('login-error');

  fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      err.style.display = 'none';
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('app').style.display = 'flex';
      document.getElementById('topbar-username').textContent = data.user.name;
      document.getElementById('topbar-role').textContent = data.user.role.toUpperCase();
      document.getElementById('welcome-name').textContent = data.user.name;
    } else {
      err.style.display = 'block';
      document.getElementById('input-pass').value = '';
    }
  });
}

function doLogout() {
  fetch('/api/auth/logout', { method: 'POST' })
  .then(() => {
    document.getElementById('login-screen').style.display = 'flex';
    document.getElementById('app').style.display = 'none';
    document.getElementById('input-email').value = '';
    document.getElementById('input-pass').value = '';
  });
}
</script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
