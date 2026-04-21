# frontend/views/pantalla_vendedor.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebSockets import QWebSocket
import json

# Importaciones de nuestras vistas y componentes
from frontend.views.crear_orden import CreateOrderWindow
from frontend.components.modulo_consulta import ModuloConsulta
from frontend.components.menu_lateral import Sidebar
from frontend.views.crear_cotizacion import CreateQuotationWindow 

class PosWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        
        # Conexión WebSocket para actualizaciones en tiempo real
        self.ws = QWebSocket()
        self.ws.textMessageReceived.connect(self.al_recibir_notificacion)
        self.ws.open(QUrl("ws://localhost:8765"))
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Punto de Venta - Vendedor: {self.user_data['nombre']}")
        self.showMaximized()
        self.setStyleSheet("background-color: #f5f6fa;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. MENÚ LATERAL (Sidebar Reutilizable)
        # ==========================================
        opciones_menu = {
            "Órdenes de Venta": lambda: self.cambiar_vista("Órdenes de Venta"),
            "Cotizaciones": lambda: self.cambiar_vista("Cotizaciones"),
            "Directorio Clientes": lambda: print("Abriendo directorio..."),
            "Cerrar Sesión": self.close
        }
        
        # Instanciamos el sidebar y lo agregamos al layout principal
        self.sidebar = Sidebar("EL TORNILLO FELIZ\nPOS", opciones_menu)
        main_layout.addWidget(self.sidebar)

        # ==========================================
        # 2. ÁREA CENTRAL (Contenedor Principal)
        # ==========================================
        content_area = QWidget()
        self.content_layout = QVBoxLayout(content_area) 
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Botón general para crear nueva orden arriba de todo
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_nuevo = QPushButton("+ Nueva Orden / Cotización")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            background-color: #27ae60; color: white; 
            padding: 10px 20px; border-radius: 5px; 
            font-weight: bold; font-size: 14px;
        """)
        self.btn_nuevo.clicked.connect(self.abrir_formulario_creacion)
        top_bar.addWidget(self.btn_nuevo)
        self.content_layout.addLayout(top_bar)

        # ==========================================
        # 3. MÓDULOS DE CONSULTA (Ventas y Cotizaciones)
        # ==========================================
        
        # Consulta de Ventas (TO_CHAR quita los microsegundos)
        query_ventas = """
            SELECT v.folio, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), c.nombre_completo, v.total, v.estatus
            FROM orden_venta v
            JOIN clientes c ON v.id_cliente = c.id_cliente
            WHERE v.fecha = %s AND v.estatus = 'Pendiente'
            ORDER BY v.hora DESC
        """
        self.modulo_ventas = ModuloConsulta(
            titulo="ÓRDENES DE VENTA PENDIENTES DEL DÍA", 
            columnas=["Folio", "Fecha", "Hora", "Cliente", "Importe", "Estatus"], 
            query_base=query_ventas,
            on_edit_callback=self.abrir_editor_orden # Al hacer doble clic, llama a esta función
        )

        # Consulta de Cotizaciones (TO_CHAR quita los microsegundos)
        query_cots = """
            SELECT v.folio, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), c.nombre_completo, v.total
            FROM cotizaciones v
            JOIN clientes c ON v.id_cliente = c.id_cliente
            WHERE v.fecha = %s 
            ORDER BY v.hora DESC
        """
        self.modulo_cotizaciones = ModuloConsulta(
            titulo="COTIZACIONES DEL DÍA", 
            columnas=["Folio", "Fecha", "Hora", "Cliente", "Importe"], 
            query_base=query_cots,
            on_edit_callback=self.abrir_editor_orden # Al hacer doble clic, llama a esta función
        )

        # Añadimos los módulos al layout de contenido
        self.content_layout.addWidget(self.modulo_ventas)
        self.content_layout.addWidget(self.modulo_cotizaciones)
        
        # Ocultamos cotizaciones por defecto al iniciar
        self.modulo_cotizaciones.hide()
        self.sidebar.resaltar_boton("Órdenes de Venta")

        main_layout.addWidget(content_area)

    def cambiar_vista(self, vista):
        """Maneja la visibilidad de los módulos y le avisa al Sidebar que resalte el botón"""
        self.sidebar.resaltar_boton(vista)
        
        if vista == "Órdenes de Venta":
            self.modulo_cotizaciones.hide()
            self.modulo_ventas.show()
            self.modulo_ventas.cargar_datos_del_dia()
        elif vista == "Cotizaciones":
            self.modulo_ventas.hide()
            self.modulo_cotizaciones.show()
            self.modulo_cotizaciones.cargar_datos_del_dia()

    def abrir_formulario_creacion(self):
        """Abre la ventana para crear órdenes/cotizaciones nuevas"""
        dialog = CreateOrderWindow(self.user_data, self)
        if dialog.exec():
            self.modulo_ventas.cargar_datos_del_dia()
            self.modulo_cotizaciones.cargar_datos_del_dia()

    def abrir_editor_orden(self, folio):
        """Se ejecuta al hacer doble clic. Abre el formulario con los datos cargados."""
        # Pasamos el folio a la ventana
        dialog = CreateOrderWindow(self.user_data, self, folio_editar=folio)
        
        # Si el usuario editó y guardó, refrescamos las tablas
        if dialog.exec():
            self.modulo_ventas.cargar_datos_del_dia()
            self.modulo_cotizaciones.cargar_datos_del_dia()

    def al_recibir_notificacion(self, mensaje):
        """WebSockets: Actualiza la tabla si otro vendedor crea algo"""
        datos = json.loads(mensaje)
        if datos["tipo"] == "NUEVA_ORDEN":
            self.modulo_ventas.cargar_datos_del_dia()
        elif datos["tipo"] == "NUEVA_COTIZACION":
            self.modulo_cotizaciones.cargar_datos_del_dia()