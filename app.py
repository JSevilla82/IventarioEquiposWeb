import os
import io
import sys
import re
from flask import Flask, render_template, request, session, g
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# --- Carga de Módulos de la Aplicación ---
from database import db_manager
from gestion_acceso import (login, menu_usuarios, cambiar_contrasena_usuario, 
                            inicializar_admin_si_no_existe, ROLES_PERMISOS, 
                            menu_configuracion_sistema, menu_ver_log_sistema, 
                            menu_gestion_acceso_sistema) # Importamos el menú
from gestion_inventario import (registrar_equipo, gestionar_equipos, 
                                menu_gestionar_pendientes, menu_gestion_inventario)
from gestion_reportes import menu_ver_inventario
from estadisticas import mostrar_estadisticas

load_dotenv()

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'un-secreto-muy-seguro-para-desarrollo')
socketio = SocketIO(app)

# --- Redirección de Salida Estándar ---
class SocketIOStdOut:
    def __init__(self, sid):
        self.sid = sid

    def write(self, message):
        clean_message = re.sub(r'\x1b\[.*?m', '', message)
        if clean_message.strip('\n '):
            socketio.emit('terminal_output', {'data': clean_message}, room=self.sid)

    def flush(self):
        pass

# --- Manejador de Sesión y Estado ---
class AppStateManager:
    def __init__(self, sid):
        self.sid = sid
        # Usamos 'g' de Flask para gestionar stdout de forma segura en cada petición
        if not hasattr(g, 'original_stdout'):
            g.original_stdout = sys.stdout
        sys.stdout = SocketIOStdOut(self.sid)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        # Restaura stdout al finalizar el bloque 'with'
        sys.stdout = g.original_stdout

    def get(self, key, default=None): return session.get(key, default)
    def set(self, key, value): session[key] = value
    def clear(self): session.clear()

    def process_input(self, user_input):
        """Función central que decide qué hacer con la entrada del usuario."""
        current_state = self.get('estado', 'login_user')
        
        state_handlers = {
            'login_user': self.handle_login_user,
            'login_pass': self.handle_login_pass,
            'menu_principal': self.handle_main_menu,
            'menu_acceso_sistema': self.handle_menu_acceso_sistema, # <-- ¡NUEVO ESTADO!
        }

        handler = state_handlers.get(current_state)
        if handler:
            handler(user_input)
        else:
            self.start_login()

    def start_login(self):
        self.clear()
        self.set('estado', 'login_user')
        print("¡Bienvenido al Control de Inventario de Equipos (CIE)!")
        print("-" * 60)
        emit('request_input', {'prompt': '👤 Ingrese su usuario: '})

    def handle_login_user(self, username):
        self.set('login_username', username)
        self.set('estado', 'login_pass')
        emit('request_input', {'prompt': '🔑 Ingrese su contraseña: '})

    def handle_login_pass(self, password):
        username = self.get('login_username')
        usuario_logueado = login(username, password)

        if usuario_logueado:
            self.set('usuario_logueado', usuario_logueado)
            user_data = db_manager.get_user_by_username(usuario_logueado)
            self.set('rol', user_data['rol'])
            self.set('estado', 'menu_principal')
            self.show_main_menu()
        else:
            intentos = self.get('intentos', 0) + 1
            self.set('intentos', intentos)
            if intentos >= 3:
                print("\n❌ Demasiados intentos fallidos. Conexión terminada.")
                socketio.disconnect(self.sid)
            else:
                print("\n❌ Credenciales incorrectas. Intente de nuevo.")
                self.start_login()

    def show_main_menu(self):
        print("\n--- MENÚ PRINCIPAL ---")
        opciones = [
            "1. Estadísticas de Inventario",
            "2. Gestión de Inventario",
            "3. Ver Inventario y Reportes",
            "4. Gestión de Acceso y Sistema",
            "5. Salir"
        ]
        print("\n".join(opciones))
        self.set('estado', 'menu_principal')
        emit('request_input', {'prompt': 'Seleccione una opción: '})

    def handle_main_menu(self, option):
        usuario = self.get('usuario_logueado')
        
        if option == '1':
            mostrar_estadisticas(usuario)
            self.show_main_menu()
        elif option == '2':
            menu_gestion_inventario(usuario)
            self.show_main_menu() # Temporalmente vuelve al menú principal
        elif option == '3':
            menu_ver_inventario(usuario)
            self.show_main_menu() # Temporalmente vuelve al menú principal
        elif option == '4':
            # MEJORA: Cambiamos al nuevo estado para manejar el submenú
            self.set('estado', 'menu_acceso_sistema')
            menu_gestion_acceso_sistema(usuario)
            emit('request_input', {'prompt': 'Seleccione una opción del submenú: '})
        elif option == '5':
            print("¡Gracias por usar el sistema! Desconectando...")
            socketio.disconnect(self.sid)
        else:
            print("\n❌ Opción no válida.")
            self.show_main_menu()

    def handle_menu_acceso_sistema(self, option):
        """Manejador para las opciones del submenú de acceso."""
        usuario = self.get('usuario_logueado')
        
        # Mapeo de opciones del submenú
        actions = {
            '1': menu_usuarios,
            '2': menu_configuracion_sistema,
            '3': menu_ver_log_sistema,
            '4': cambiar_contrasena_usuario,
        }

        if option == '5': # Opción para volver
            self.show_main_menu()
            return
        
        action = actions.get(option)
        if action:
            action(usuario)
        else:
            print("\n❌ Opción no válida.")

        # Después de ejecutar la acción, volvemos a mostrar el submenú
        menu_gestion_acceso_sistema(usuario)
        emit('request_input', {'prompt': 'Seleccione una opción del submenú: '})

# --- Rutas y Eventos de Socket.IO ---
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    with app.app_context(): # Usamos el contexto de la aplicación
        with AppStateManager(request.sid) as state:
            print(f"Nuevo cliente conectado: {request.sid}")
            state.start_login()

@socketio.on('terminal_input')
def handle_terminal_input(json):
    with app.app_context():
        with AppStateManager(request.sid) as state:
            user_input = json.get('data', '').strip()
            state.process_input(user_input)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Cliente desconectado: {request.sid}")

# --- Punto de Entrada ---
if __name__ == '__main__':
    inicializar_admin_si_no_existe()
    print("Iniciando servidor Flask en http://127.0.0.1:5000")
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)