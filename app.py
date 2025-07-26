import os
import io
import sys
import re
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# --- Carga de Módulos de la Aplicación ---
# Se importan las funciones que contienen la lógica de negocio.
# Las hemos adaptado ligeramente para que funcionen en este entorno.
from database import db_manager
from gestion_acceso import (login, menu_usuarios, cambiar_contrasena_usuario, 
                            inicializar_admin_si_no_existe, ROLES_PERMISOS, 
                            menu_configuracion_sistema, menu_ver_log_sistema)
from gestion_inventario import (registrar_equipo, gestionar_equipos, 
                                menu_gestionar_pendientes)
from gestion_reportes import menu_ver_inventario
from estadisticas import mostrar_estadisticas

# Cargar variables de entorno (útil para claves secretas)
load_dotenv()

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'un-secreto-muy-seguro-para-desarrollo')
socketio = SocketIO(app)

# --- Redirección de Salida Estándar ---
# Esta clase es la "magia" que nos permite usar tus funciones existentes.
# Captura todo lo que normalmente se imprimiría en la consola (con print)
# y lo redirige al navegador del usuario correcto.
class SocketIOStdOut:
    def __init__(self, sid):
        self.sid = sid

    def write(self, message):
        # Limpiamos los códigos de color de 'colorama' para que no se vean en HTML.
        clean_message = re.sub(r'\x1b\[.*?m', '', message)
        if clean_message.strip():
            socketio.emit('terminal_output', {'data': clean_message}, room=self.sid)

    def flush(self):
        pass # Requerido por la interfaz de stream, no necesita hacer nada aquí.

# --- Manejador de Sesión y Estado ---
# Cada usuario conectado tendrá su propia "máquina de estados" en su sesión.
# Esto nos permite saber en qué parte del menú se encuentra cada usuario.
class AppStateManager:
    def __init__(self, sid):
        self.sid = sid
        # Usamos g de Flask para almacenar una copia de stdout por petición
        g.original_stdout = sys.stdout
        sys.stdout = SocketIOStdOut(self.sid)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = g.original_stdout # Restauramos stdout al finalizar

    def get_state(self, key, default=None):
        return session.get(key, default)

    def set_state(self, key, value):
        session[key] = value

    def clear_session(self):
        session.clear()

    def process_input(self, user_input):
        """Función central que decide qué hacer con la entrada del usuario."""
        current_state = self.get_state('estado', 'login_user')
        
        # Mapeo de estados a funciones manejadoras
        state_handlers = {
            'login_user': self.handle_login_user,
            'login_pass': self.handle_login_pass,
            'menu_principal': self.handle_main_menu,
            # Futuros estados de sub-menús irían aquí
        }

        handler = state_handlers.get(current_state)
        if handler:
            handler(user_input)
        else:
            # Si el estado es desconocido, reiniciamos al login.
            self.start_login()

    # --- Manejadores de Estado Específicos ---

    def start_login(self):
        self.clear_session()
        self.set_state('estado', 'login_user')
        print("¡Bienvenido al Control de Inventario de Equipos (CIE)!")
        print("-" * 60)
        emit('request_input', {'prompt': '👤 Ingrese su usuario: '})

    def handle_login_user(self, username):
        self.set_state('login_username', username)
        self.set_state('estado', 'login_pass')
        emit('request_input', {'prompt': '🔑 Ingrese su contraseña: '})

    def handle_login_pass(self, password):
        username = self.get_state('login_username')
        # La función 'login' original fue adaptada para no tener bucles ni input.
        usuario_logueado = login(username, password)

        if usuario_logueado:
            self.set_state('usuario_logueado', usuario_logueado)
            user_data = db_manager.get_user_by_username(usuario_logueado)
            self.set_state('rol', user_data['rol'])
            self.set_state('estado', 'menu_principal')
            self.show_main_menu()
        else:
            intentos = self.get_state('intentos', 0) + 1
            self.set_state('intentos', intentos)
            if intentos >= 3:
                print("\n❌ Demasiados intentos fallidos. La conexión se cerrará.")
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
        self.set_state('estado', 'menu_principal')
        emit('request_input', {'prompt': 'Seleccione una opción: '})

    def handle_main_menu(self, option):
        usuario = self.get_state('usuario_logueado')
        
        menu_actions = {
            '1': mostrar_estadisticas,
            '2': menu_gestion_inventario,
            '3': menu_ver_inventario,
            '4': menu_gestion_acceso_sistema, # Esta función ahora mostrará su propio sub-menú
        }

        if option == '5':
            print("¡Gracias por usar el sistema! Desconectando...")
            socketio.disconnect(self.sid)
            return

        action = menu_actions.get(option)
        if action:
            # Llamamos a la función correspondiente, que ahora imprimirá su propio menú.
            # La adaptación clave es que estas funciones ahora necesitarán solicitar
            # input a través de un nuevo mecanismo. Por ahora, las que no son interactivas
            # funcionarán directamente.
            
            # --- MEJORA ---
            # En un futuro, haríamos que estas funciones retornen el siguiente estado
            # en lugar de manejar el bucle ellas mismas. Por ahora, las dejamos
            # que impriman su contenido y luego volvemos al menú principal.
            action(usuario)
        else:
            print("\n❌ Opción no válida.")
        
        # Después de cada acción, volvemos al menú principal.
        self.show_main_menu()


# --- Eventos de Socket.IO ---

@app.route('/')
def index():
    """Sirve la página principal que contiene la terminal web."""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Se ejecuta cuando un nuevo usuario se conecta."""
    with AppStateManager(request.sid) as state:
        print(f"Nuevo cliente conectado: {request.sid}")
        state.start_login()

@socketio.on('terminal_input')
def handle_terminal_input(json):
    """Se ejecuta cuando el usuario envía un comando desde el navegador."""
    with AppStateManager(request.sid) as state:
        user_input = json.get('data', '').strip()
        state.process_input(user_input)

@socketio.on('disconnect')
def handle_disconnect():
    """Se ejecuta cuando un usuario se desconecta."""
    print(f"Cliente desconectado: {request.sid}")


# --- Punto de Entrada de la Aplicación ---
if __name__ == '__main__':
    # Asegurarse de que el usuario 'admin' inicial exista.
    inicializar_admin_si_no_existe()
    print("Iniciando servidor Flask en http://127.0.0.1:5000")
    # `allow_unsafe_werkzeug=True` es necesario para versiones recientes de Flask con SocketIO
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)