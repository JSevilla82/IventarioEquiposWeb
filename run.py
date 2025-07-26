from app import create_app

# Creamos una instancia de nuestra aplicación llamando a la factory
app = create_app()

if __name__ == '__main__':
    # Ejecutamos el servidor de desarrollo de Flask
    # debug=True hace que el servidor se reinicie automáticamente con cada cambio.
    app.run(debug=True, port=5001)