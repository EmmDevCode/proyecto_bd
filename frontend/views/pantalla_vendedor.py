# frontend/views/pantalla_vendedor.py
import qtawesome as qta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebSockets import QWebSocket
import json
from frontend.views.crear_orden import CreateOrderWindow
from frontend.components.modulo_consulta import ModuloConsulta
from frontend.components.menu_lateral import Sidebar
from frontend.views.crear_cotizacion import CreateQuotationWindow

class PosWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        
    
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

  
        opciones_menu = {
            "Órdenes de Venta": lambda: self.cambiar_vista("Órdenes de Venta"),
            "Cotizaciones": lambda: self.cambiar_vista("Cotizaciones"),
            "Cerrar Sesión": self.close
        }
        
        self.sidebar = Sidebar("EL TORNILLO FELIZ\nPOS", opciones_menu)
        main_layout.addWidget(self.sidebar)

     
        content_area = QWidget()
        self.content_layout = QVBoxLayout(content_area) 
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(Qt.GlobalColor.lightGray)
        shadow.setOffset(0, 2)
        header_frame.setGraphicsEffect(shadow)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(40, 20, 40, 20)
        
        self.lbl_titulo_seccion = QLabel("ÓRDENES DE VENTA")
        self.lbl_titulo_seccion.setStyleSheet("""
            font-size: 16pt;
            font-weight: 800;
            color: #1e293b;
            font-family: 'Segoe UI', system-ui, sans-serif;
            border: none;
            letter-spacing: 1px;
        """)
        header_layout.addWidget(self.lbl_titulo_seccion)
        
        header_layout.addStretch()
        
        self.btn_nuevo = QPushButton("  Nueva Orden / Cotización")
        try:
            self.btn_nuevo.setIcon(qta.icon('fa5s.plus', color='white'))
        except Exception:
            pass
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #10b981; 
                color: white; 
                border: none;
                padding: 12px 24px; 
                border-radius: 8px; 
                font-weight: 700; 
                font-size: 11pt;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        self.btn_nuevo.clicked.connect(self.abrir_formulario_creacion)
        header_layout.addWidget(self.btn_nuevo)
        
        self.content_layout.addWidget(header_frame)

      
        body_area = QWidget()
        self.body_layout = QVBoxLayout(body_area)
        self.body_layout.setContentsMargins(40, 30, 40, 30)
        self.body_layout.setSpacing(20)
        
        self.content_layout.addWidget(body_area)


        query_ventas = """
            SELECT v.folio, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), c.nombre_completo, v.cliente_temporal, v.total, v.estatus
            FROM orden_venta v
            JOIN clientes c ON v.id_cliente = c.id_cliente
            WHERE v.fecha = %s AND v.estatus = 'Pendiente'
            ORDER BY v.hora DESC
        """
        self.modulo_ventas = ModuloConsulta(
            titulo="ÓRDENES DE VENTA PENDIENTES DEL DÍA", 
            columnas=["Folio", "Fecha", "Hora", "Cliente", "Nombre/Seña", "Importe", "Estatus"], 
            query_base=query_ventas,
            action_callback=self.abrir_editor_orden
        )

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
            action_callback=self.abrir_editor_orden
        )

        self.body_layout.addWidget(self.modulo_ventas)
        self.body_layout.addWidget(self.modulo_cotizaciones)
        
        self.modulo_cotizaciones.hide()
        self.sidebar.resaltar_boton("Órdenes de Venta")

        main_layout.addWidget(content_area)

    def cambiar_vista(self, vista):
        self.sidebar.resaltar_boton(vista)
        self.lbl_titulo_seccion.setText(vista.upper())
        
        if vista == "Órdenes de Venta":
            self.modulo_cotizaciones.hide()
            self.modulo_ventas.show()
            self.modulo_ventas.cargar_datos_del_dia()
        elif vista == "Cotizaciones":
            self.modulo_ventas.hide()
            self.modulo_cotizaciones.show()
            self.modulo_cotizaciones.cargar_datos_del_dia()

    def abrir_formulario_creacion(self):
        if self.modulo_cotizaciones.isVisible():
            dialog = CreateQuotationWindow(self.user_data, self)
        else:
            dialog = CreateOrderWindow(self.user_data, self)
            
        if dialog.exec():
            if hasattr(dialog, 'folio_generado'):
                self.ws.sendTextMessage(json.dumps({"tipo": "NUEVA_ORDEN", "folio": dialog.folio_generado}))
            self.modulo_ventas.cargar_datos_del_dia()
            self.modulo_cotizaciones.cargar_datos_del_dia()

    def abrir_editor_orden(self, folio):
        if folio.startswith("COT-"):
            dialog = CreateQuotationWindow(self.user_data, self, folio_editar=folio)
        else:
            dialog = CreateOrderWindow(self.user_data, self, folio_editar=folio)
            
        if dialog.exec():
            if hasattr(dialog, 'folio_generado'):
                self.ws.sendTextMessage(json.dumps({"tipo": "NUEVA_ORDEN", "folio": dialog.folio_generado}))
            self.modulo_ventas.cargar_datos_del_dia()
            self.modulo_cotizaciones.cargar_datos_del_dia()

    def al_recibir_notificacion(self, mensaje):
        datos = json.loads(mensaje)
        
        if datos["tipo"] in ["NUEVA_ORDEN", "ORDEN_COBRADA"]:
            self.modulo_ventas.cargar_datos_del_dia()
        elif datos["tipo"] == "NUEVA_COTIZACION":
            self.modulo_cotizaciones.cargar_datos_del_dia()