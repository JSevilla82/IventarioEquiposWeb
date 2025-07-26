# estadisticas.py
from datetime import datetime
# MEJORA: Ya no se necesita colorama aquí directamente, pero lo dejamos por si se usa en el futuro.
from colorama import Fore, Style, init

from database import db_manager

# Inicializar colorama (buena práctica mantenerlo)
init(autoreset=True)

def obtener_color_por_cantidad(cantidad, umbral_bajo=1, umbral_alto=5):
    """Devuelve un color de texto basado en la cantidad (sin cambios)."""
    # Esta función no usa print, por lo que no necesita cambios.
    # Sin embargo, como el HTML no renderiza colores de consola,
    # el efecto visual se perderá. Podríamos mejorarlo en el futuro.
    if cantidad == 0:
        return "" # Verde en consola
    elif cantidad <= umbral_bajo:
        return "" # Amarillo en consola
    else:
        return "" # Rojo en consola

def mostrar_estadisticas(usuario: str):
    """
    Muestra el panel de control con un resumen del inventario (adaptado para web).
    """
    # ELIMINADO: Las llamadas a os.system y mostrar_encabezado
    # La función ahora solo se encarga de imprimir su contenido.
    print("\n--- Estadísticas de Inventario ---")

    # --- 1. Obtención de Datos (sin cambios) ---
    equipos = db_manager.get_all_equipos()
    
    estados = {
        "Disponible": 0, "Asignado": 0, "En préstamo": 0, "En mantenimiento": 0,
        "Pendiente Devolución a Proveedor": 0, "Devuelto a Proveedor": 0, "Renovación": 0,
    }
    for equipo in equipos:
        if equipo['estado'] in estados:
            estados[equipo['estado']] += 1
    
    total_equipos_activos = sum(v for k, v in estados.items() if k not in ["Devuelto a Proveedor", "Renovación"])
    movimientos_recientes = db_manager.get_all_log_inventario()[:10]

    # --- 2. Renderizado del Dashboard (solo con print) ---
    
    print("\n--- Resumen General del Inventario ---")
    print(f"  Total de Equipos Activos: {total_equipos_activos}")
    print(f"  Equipos en Renovación: {estados['Renovación']}")
    print(f"  Equipos Devueltos a Proveedor: {estados['Devuelto a Proveedor']}")
    print("-" * 40)

    print("\n--- Estado Actual de Equipos Activos ---")
    print(f"  Disponibles: .................... {estados['Disponible']}")
    print(f"  Asignados: ...................... {estados['Asignado']}")
    print(f"  En Préstamo: .................... {estados['En préstamo']}")
    print("-" * 40)

    print("\n--- Procesos Pendientes de Aprobación ---")
    print(f"  En Mantenimiento: ............... {estados['En mantenimiento']}")
    print(f"  Pendientes de Devolución: ....... {estados['Pendiente Devolución a Proveedor']}")
    print(f"  En Renovación: .................. {estados['Renovación']}")
    print("-" * 40)

    print(f"\n--- Últimos {len(movimientos_recientes)} Movimientos del Inventario ---")
    if not movimientos_recientes:
        print("  No se han registrado movimientos recientemente.")
    else:
        print(f"  {'FECHA':<20} {'PLACA':<15} {'ACCIÓN':<30} {'USUARIO'}")
        print(f"  {'-'*18} {'-'*13} {'-'*28} {'-'*15}")
        for mov in movimientos_recientes:
            fecha_obj = datetime.strptime(mov['fecha'], "%Y-%m-%d %H:%M:%S")
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
            accion = mov['accion']
            if len(accion) > 28:
                accion = accion[:27] + "..."
            print(f"  {fecha_formateada:<20} {mov['equipo_placa']:<15} {accion:<30} {mov['usuario']}")
    
    # ELIMINADO: La llamada a pausar_pantalla(). El flujo ahora lo controla app.py.