# frontend/views/pantalla_admin.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel
from PyQt6.QtCore import Qt
import qtawesome as qta

from frontend.components.menu_lateral import Sidebar
from frontend.components.modulo_consulta import ModuloConsulta
from frontend.views.pantalla_vendedor import PosWindow
from frontend.views.pantalla_caja import CajaWindow
from frontend.components.alertas import AlertaCustom
from frontend.views.modulo_compras import ModuloCompras
from frontend.views.modulo_catalogo import ModuloCatalogo
from frontend.views.modulo_almacenes import ModuloAlmacenes
from frontend.views.modulo_clientes import ModuloClientes
from frontend.views.modulo_proveedores import ModuloProveedores
from frontend.views.modulo_empleados import ModuloEmpleados
from frontend.views.modulo_reportes import ModuloReportes

class AdminWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Administración Ferrosoft - {self.user_data['nombre']}")
        self.showMaximized()
        self.setStyleSheet("background-color: #f5f6fa;")
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. EL ÚNICO MENÚ DEL SISTEMA (Control Remoto)
        # ==========================================
        config_menu = {
            (qta.icon('fa5s.home', color='#bdc3c7'), "Dashboard"): lambda: self.cambiar_vista_admin(0),
            
            (qta.icon('fa5s.shopping-cart', color='#bdc3c7'), "VENTAS"): {
                "Órdenes de Venta": lambda: self.navegar_hijo(1, "Órdenes de Venta"), 
                "Cotizaciones": lambda: self.navegar_hijo(1, "Cotizaciones")
            },
            
            (qta.icon('fa5s.cash-register', color='#bdc3c7'), "CAJA"): {
                "Fila de Cobro": lambda: self.navegar_hijo(2, "Órdenes Pendientes"),
                "Historial del Día": lambda: self.navegar_hijo(2, "Ventas Cobradas")
            },
            
            (qta.icon('fa5s.clipboard-list', color='#bdc3c7'), "AUDITORÍA"): {
                "Cortes de Caja Globales": lambda: self.cambiar_vista_admin(3),
                "Métricas y Reportes": lambda: self.cambiar_vista_admin(4)
            },
            
            (qta.icon('fa5s.boxes', color='#bdc3c7'), "INVENTARIO Y COMPRAS"): {
                "Catálogo de Productos": lambda: self.cambiar_vista_admin(5), 
                "Historial de Compras": lambda: self.cambiar_vista_admin(6),
                "Gestión de Almacenes": lambda: self.cambiar_vista_admin(7)
            },
            
            (qta.icon('fa5s.users', color='#bdc3c7'), "DIRECTORIOS Y PERSONAL"): {
                "Gestión de Clientes": lambda: self.cambiar_vista_admin(8),
                "Gestión de Proveedores": lambda: self.cambiar_vista_admin(9),
                "Gestión de Personal": lambda: self.cambiar_vista_admin(10)
            },
            
            (qta.icon('fa5s.sign-out-alt', color='#bdc3c7'), "Cerrar Sesión"): self.close
        }

        self.sidebar = Sidebar("FERROSOFT ADMIN", config_menu)
        main_layout.addWidget(self.sidebar)

        # ==========================================
        # 2. CONTENEDOR DE VISTAS (Stacked Widget)
        # ==========================================
        self.vistas = QStackedWidget()
        
        # --- Vista 0: Dashboard ---
        self.vistas.addWidget(self.crear_dashboard_bienvenida())
        
        # --- Vista 1: Modo Vendedor ---
        self.vista_ventas = PosWindow(self.user_data)
        self.vista_ventas.sidebar.hide()
        self.vistas.addWidget(self.vista_ventas)
        
        # --- Vista 2: Modo Caja ---
        self.vista_caja = CajaWindow(self.user_data)
        self.vista_caja.sidebar.hide()
        self.vistas.addWidget(self.vista_caja)
        
        # --- Vista 3: Auditoría de Cortes de Caja ---
        query_cortes = """
            SELECT c.id_corte, e.nombre_completo, 
                   TO_CHAR(c.fecha_hora_apertura, 'DD/MM HH24:MI'),
                   COALESCE(TO_CHAR(c.fecha_hora_cierre, 'DD/MM HH24:MI'), 'En turno'),
                   c.fondo_inicial, COALESCE(c.total_sistema, 0), COALESCE(c.diferencia, 0), c.estatus
            FROM cortes_caja c
            JOIN empleados e ON c.id_cajero = e.id_empleado
            ORDER BY c.fecha_hora_apertura DESC
        """
        self.modulo_auditoria = ModuloConsulta(
            titulo="HISTORIAL GLOBAL DE CORTES DE CAJA",
            columnas=["ID", "Cajero", "Apertura", "Cierre", "Fondo", "Sistema", "Diferencia", "Estatus"],
            query_base=query_cortes
        )
        self.vistas.addWidget(self.modulo_auditoria)

        # --- Vista 4: Reportes Analíticos (EL NUEVO DASHBOARD) ---
        # (Eliminamos el código viejo de query_ventas_global)
        self.vista_reportes = ModuloReportes()
        self.vistas.addWidget(self.vista_reportes)

        # --- Vista 5: Catálogo de Productos ---
        self.vista_catalogo = ModuloCatalogo()
        self.vistas.addWidget(self.vista_catalogo)

        # --- Vista 6: Compras ---
        self.vista_compras = ModuloCompras()
        self.vistas.addWidget(self.vista_compras)

        # --- Vista 7: Almacenes ---
        self.vista_almacenes = ModuloAlmacenes()
        self.vistas.addWidget(self.vista_almacenes)

        # --- Vista 8: Clientes ---
        self.vista_clientes = ModuloClientes()
        self.vistas.addWidget(self.vista_clientes)

        # --- Vista 9: Proveedores ---
        self.vista_proveedores = ModuloProveedores()
        self.vistas.addWidget(self.vista_proveedores)

        # --- Vista 10: Empleados ---
        self.vista_empleados = ModuloEmpleados()
        self.vistas.addWidget(self.vista_empleados) 

        main_layout.addWidget(self.vistas)

    # ==========================================
    # FUNCIONES DE UI Y NAVEGACIÓN
    # ==========================================
    def crear_dashboard_bienvenida(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_titulo = QLabel("Panel de Control Gerencial")
        lbl_titulo.setStyleSheet("font-size: 32px; color: #2c3e50; font-weight: bold;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_sub = QLabel(f"Bienvenido, {self.user_data['nombre']}.\nSelecciona una opción del menú lateral para comenzar.")
        lbl_sub.setStyleSheet("font-size: 18px; color: #7f8c8d; margin-top: 10px;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_sub)
        return widget

    def cambiar_vista_admin(self, indice):
        """Mueve el StackedWidget a las vistas exclusivas del admin (0, 3, 4)"""
        self.vistas.setCurrentIndex(indice)
        try:
            if indice == 3: self.modulo_auditoria.cargar_datos_del_dia()
            elif indice == 4: self.modulo_reporte_ventas.cargar_datos_del_dia()
        except Exception: pass

    def navegar_hijo(self, indice_ventana, nombre_vista_interna):
        """Usa el control remoto para decirle a la Caja o al Vendedor qué pestaña mostrar"""
        self.vistas.setCurrentIndex(indice_ventana)
        
        if indice_ventana == 1:
            # Revisa en tu archivo pantalla_vendedor.py que strings usaste en cambiar_vista
            # Ejemplo: Si usaste "Cotizaciones", el menú arriba debe decir exactamente eso.
            try: self.vista_ventas.cambiar_vista(nombre_vista_interna)
            except Exception as e: print(f"Error cambiando vista vendedor: {e}")
            
        elif indice_ventana == 2:
            try: self.vista_caja.cambiar_vista(nombre_vista_interna)
            except Exception as e: print(f"Error cambiando vista caja: {e}")