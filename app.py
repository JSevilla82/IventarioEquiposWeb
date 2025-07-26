import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv

def create_app():
    """
    Crea y configura una instancia de la aplicación Flask.
    """
    app = Flask(__name__)
    
    load_dotenv()
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # --- RUTAS DE LA APLICACIÓN ---

    @app.route('/')
    def index():
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if username == 'admin' and password == 'adminpass':
                session['username'] = username
                session['rol'] = 'Administrador'
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos.', 'error')
                return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard():
        if 'username' not in session:
            flash('Debes iniciar sesión para ver esta página.', 'error')
            return redirect(url_for('login'))
        
        # CAMBIO: Ahora renderiza la nueva plantilla del panel
        return render_template('dashboard.html')

    return app