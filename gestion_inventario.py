# gestion_inventario.py
import re
import textwrap
from datetime import datetime
from typing import Optional, List

# Se usa la sesión de Flask para obtener el rol del usuario
from flask import session

from database import db_manager, Equipo, registrar_movimiento_inventario
from gestion_acceso import requiere_permiso, ROLES_PERMISOS
from gestion_reportes import generar_excel_historico_equipo

# --- MENÚ PRINCIPAL DEL MÓDULO ---

def menu_gestion_inventario(usuario: str):
    """Muestra las opciones del módulo de gestión de inventario."""
    print("\n--- Módulo de Gestión de Inventario ---")
    rol_actual = session.get('rol', 'Visualizador')
    
    opciones_disponibles = []
    
    if "registrar_equipo" in ROLES_PERMISOS[rol_actual]: 
        opciones_disponibles.append("1. Registrar nuevo equipo")
    if "gestionar_equipo" in ROLES_PERMISOS[rol_actual]: 
        opciones_disponibles.append("2. Gestionar Equipos")
    if "gestionar_pendientes" in ROLES_PERMISOS[rol_actual]:
        equipos = db_manager.get_all_equipos()
        mantenimientos = len([e for e in equipos if e.get('estado') == "En mantenimiento"])
        devoluciones = len([e for e in equipos if e.get('estado') == "Pendiente Devolución a Proveedor"])
        renovaciones = len([e for e in equipos if e.get('estado') == "Renovación"])
        total_pendientes = mantenimientos + devoluciones + renovaciones
        
        texto_pendientes = f"3. Gestionar Mantenimientos y Devoluciones ({total_pendientes} Pendientes)"
        opciones_disponibles.append(texto_pendientes)
    
    opciones_disponibles.append("4. Volver al menú principal")

    print("\n".join(opciones_disponibles))
    # La lógica para manejar la opción del usuario se gestionará en app.py

# --- FUNCIONES DE UTILIDAD Y VALIDACIÓN (Sin cambios) ---
def validar_placa_unica(placa: str) -> bool:
    return db_manager.get_equipo_by_placa(placa) is None

def validar_email(email: str) -> bool:
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def validar_placa_formato(placa: str) -> bool:
    return len(placa) >= 4 and placa.isalnum()

def validar_formato_fecha(fecha_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        return None
        
def calcular_antiguedad(fecha_str: str) -> str:
    if not fecha_str: return "N/A"
    try:
        fecha_inicio = datetime.strptime(fecha_str.split(" ")[0], "%Y-%m-%d")
        hoy = datetime.now()
        diferencia = abs(hoy - fecha_inicio)
        anios, dias_restantes = divmod(diferencia.days, 365)
        meses, dias = divmod(dias_restantes, 30)
        return f"{anios}a, {meses}m, {dias}d"
    except (ValueError, IndexError):
        return "Fecha inválida"

def format_wrapped_text(label: str, text: str, width: int = 90) -> str:
    label_width = len(label)
    subsequent_indent = ' ' * label_width
    wrapper = textwrap.TextWrapper(
        initial_indent=label, width=width, subsequent_indent=subsequent_indent,
        break_long_words=False, replace_whitespace=False
    )
    return wrapper.fill(text)
    
# --- FUNCIONES PRINCIPALES DE INVENTARIO (ADAPTADAS) ---

@requiere_permiso("registrar_equipo")
def registrar_equipo(usuario: str):
    """Muestra el primer paso para registrar un equipo."""
    print("\n--- Registro de Nuevo Equipo ---")
    print("Esta es una función interactiva.")
    print("Implementación completa requiere expandir la máquina de estados en app.py.")
    print("Por ahora, te mostramos cómo se vería el primer paso:")
    
    tipos = db_manager.get_parametros_por_tipo('tipo_equipo', solo_activos=True)
    marcas = db_manager.get_parametros_por_tipo('marca_equipo', solo_activos=True)

    if not tipos or not marcas:
        print("\n❌ No se puede registrar un nuevo equipo.")
        if not tipos: print("   - No hay 'Tipos de Equipo' activos configurados.")
        if not marcas: print("   - No hay 'Marcas' activas configuradas.")
        return

    print("\nPor favor, introduce la placa del equipo.")
    # En app.py, aquí se cambiaría el estado a 'registrar_equipo_placa'
    # y se solicitaría el input al usuario.

@requiere_permiso("gestionar_equipo")
def gestionar_equipos(usuario: str):
    """Muestra la lista de equipos y solicita una placa para gestionar."""
    print("\n--- Gestión de Equipos ---")
    
    print("\n--- Equipos Nuevos (sin gestión) ---")
    equipos_nuevos = db_manager.get_new_equipos()
    if equipos_nuevos:
        for equipo in equipos_nuevos:
            print(f"  - Placa: {equipo['placa']}, Tipo: {equipo['tipo']}, Marca: {equipo['marca']} (New)")
    else:
        print("  (No hay equipos nuevos)")

    print("\n--- Equipos Disponibles (con historial) ---")
    equipos_disponibles = db_manager.get_available_not_new_equipos()
    if equipos_disponibles:
        for equipo in equipos_disponibles:
            print(f"  - Placa: {equipo['placa']}, Tipo: {equipo['tipo']}, Marca: {equipo['marca']}")
    else:
        print("  (No hay equipos disponibles con historial)")

    print("\n" + "-" * 50)
    print("Introduce la placa del equipo a gestionar.")
    # En app.py, aquí se cambiaría el estado a 'gestionar_equipo_placa'
    # y se solicitaría el input al usuario.

def mostrar_detalles_equipo(placa: str):
    """Muestra una vista detallada de un equipo (función no interactiva)."""
    equipo_data = db_manager.get_equipo_by_placa(placa)
    if not equipo_data:
        print(f"\n❌ No se encontró el equipo con placa {placa}.")
        return

    equipo = Equipo(**equipo_data)
    print(f"\n--- Detalles Completos del Equipo: Placa {equipo.placa} ---")

    print("\n--- Información del Equipo ---")
    print(f"  {'Placa:'.ljust(28)} {equipo.placa}")
    print(f"  {'Tipo:'.ljust(28)} {equipo.tipo}")
    print(f"  {'Marca:'.ljust(28)} {equipo.marca}")
    print(f"  {'Modelo:'.ljust(28)} {equipo.modelo}")
    print(f"  {'Serial:'.ljust(28)} {equipo.serial}")
    print(f"  {'Fecha de Registro:'.ljust(28)} {equipo.fecha_registro}")

    print("\n--- Estado y Asignación ---")
    ultimo_movimiento = db_manager.get_last_movimiento_by_placa(equipo.placa)
    fecha_estado = ""
    if ultimo_movimiento:
        fecha_obj = datetime.strptime(ultimo_movimiento['fecha'], "%Y-%m-%d %H:%M:%S")
        fecha_estado = f" / Desde el {fecha_obj.strftime('%d/%m/%Y')}"
    print(f"  {'Estado Actual:'.ljust(28)} {equipo.estado}{fecha_estado}")

    if equipo.asignado_a:
        print(f"  {'Asignado a:'.ljust(28)} {equipo.asignado_a} ({equipo.email_asignado or 'Sin email'})")

    # ... (se podrían añadir más detalles de otros estados) ...

    print("\n--- Últimos 5 Movimientos ---")
    ultimos_movimientos = db_manager.get_log_by_placa(equipo.placa, limit=5)
    if not ultimos_movimientos:
        print("  No hay movimientos registrados para este equipo.")
    else:
        print(f"  {'FECHA':<20} {'ACCIÓN':<30} {'USUARIO':<15}")
        print(f"  {'-'*18} {'-'*28} {'-'*13}")
        for mov in ultimos_movimientos:
            fecha_obj = datetime.strptime(mov['fecha'], "%Y-%m-%d %H:%M:%S")
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
            print(f"  {fecha_formateada:<20} {mov['accion']:<30} {mov['usuario']:<15}")

@requiere_permiso("gestionar_pendientes")
def menu_gestionar_pendientes(usuario: str):
    """Muestra el menú para gestionar tareas pendientes."""
    print("\n--- Gestionar Mantenimientos, Devoluciones y Renovaciones ---")
    
    equipos = db_manager.get_all_equipos()
    mantenimientos = len([e for e in equipos if e.get('estado') == "En mantenimiento"])
    devoluciones = len([e for e in equipos if e.get('estado') == "Pendiente Devolución a Proveedor"])
    renovaciones = len([e for e in equipos if e.get('estado') == "Renovación"])

    opciones = [
        f"1. Gestionar Equipos en Mantenimiento ({mantenimientos})",
        f"2. Gestionar Devoluciones a Proveedor ({devoluciones})",
        f"3. Gestionar Renovaciones Pendientes ({renovaciones})",
        "4. Volver"
    ]
    print("\n".join(opciones))