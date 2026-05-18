# frontend/views/pantalla_caja.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebSockets import QWebSocket
import json

# Importaciones de componentes estandarizados
from frontend.components.menu_lateral import Sidebar
from frontend.components.modulo_consulta import ModuloConsulta
from frontend.components.alertas import AlertaCustom
from frontend.views.ventana_cobro import VentanaCobro 
from frontend.views.modulo_corte import ModuloCorte
from frontend.views.apertura_caja import AperturaCajaModal
from backend.bd_conexion import DatabaseConnection

class CajaWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = DatabaseConnection() 
        
        self.id_corte_activo = None
        self.fondo_inicial = 0.0
        
        # 1. Verificación de seguridad de turno
        self.verificar_apertura()
        
        # 2. Construcción de Interfaz
        self.init_ui()
        
        # 3. Sincronización en tiempo real
        self.ws = QWebSocket()
        self.ws.textMessageReceived.connect(self.al_recibir_notificacion)
        self.ws.open(QUrl("ws://localhost:8765"))

    def init_ui(self):
        self.setWindowTitle(f"Módulo de Caja - Cajero: {self.user_data['nombre']}")
        self.showMaximized()
        self.setStyleSheet("background-color: #f5f6fa;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. SIDEBAR PROFESIONAL
        # ==========================================
        import qtawesome as qta
        opciones_menu = {
            (qta.icon('fa5s.clock', color='#bdc3c7'), "Órdenes Pendientes"): lambda: self.cambiar_vista("Órdenes Pendientes"),
            (qta.icon('fa5s.history', color='#bdc3c7'), "Ventas Cobradas"): lambda: self.cambiar_vista("Ventas Cobradas"),
            (qta.icon('fa5s.cut', color='#bdc3c7'), "Corte de Caja"): lambda: self.cambiar_vista("Corte de Caja"),
            (qta.icon('fa5s.cog', color='#bdc3c7'), "Configuración Hardware"): self.abrir_configuracion,
            (qta.icon('fa5s.sign-out-alt', color='#bdc3c7'), "Cerrar Sesión"): self.close
        }
        self.sidebar = Sidebar("CAJERO", opciones_menu)
        main_layout.addWidget(self.sidebar)

        # ==========================================
        # 2. ÁREA DE TRABAJO
        # ==========================================
        content_area = QWidget()
        self.content_layout = QVBoxLayout(content_area) 
        self.content_layout.setContentsMargins(30, 30, 30, 30)

        # --- Módulo 1: Fila de Cobro con Nombre/Seña ---
        query_pendientes = """
            SELECT v.folio, TO_CHAR(v.hora, 'HH24:MI'), e.nombre_completo as vendedor, c.nombre_completo as cliente, v.cliente_temporal, v.total
            FROM orden_venta v
            JOIN clientes c ON v.id_cliente = c.id_cliente
            JOIN empleados e ON v.id_vendedor = e.id_empleado
            WHERE v.fecha = %s AND v.estatus = 'Pendiente'
            ORDER BY v.hora ASC
        """
        menu_pendientes = { "Cobrar Orden": self.abrir_ventana_cobro }

        self.modulo_pendientes = ModuloConsulta(
            titulo="FILA DE COBRO: ÓRDENES PENDIENTES", 
            columnas=["Folio", "Hora", "Vendedor", "Cliente", "Nombre/Seña", "Total"], 
            query_base=query_pendientes,
            action_callback=self.abrir_ventana_cobro,
            menu_opciones=menu_pendientes
        )

        # --- Módulo 2: Historial de Ventas Cobradas con Nombre/Seña ---
        query_cobradas = """
            SELECT v.folio, TO_CHAR(v.hora, 'HH24:MI'), c.nombre_completo, v.cliente_temporal, v.total, v.estatus
            FROM orden_venta v
            JOIN clientes c ON v.id_cliente = c.id_cliente
            WHERE v.fecha = %s AND v.estatus = 'Cobrada'
            ORDER BY v.hora DESC
        """
        menu_cobradas = {
            "Ver Detalles": self.ver_detalle_cobrada,
            "Reimprimir Ticket": self.reimprimir_ticket
        }

        self.modulo_cobradas = ModuloConsulta(
            titulo="HISTORIAL DE VENTAS COBRADAS", 
            columnas=["Folio", "Hora", "Cliente", "Nombre/Seña", "Total", "Estatus"], 
            query_base=query_cobradas,
            menu_opciones=menu_cobradas
        )

        # Módulo de Corte de Caja
        self.modulo_corte = ModuloCorte(self.user_data, self.id_corte_activo, self.fondo_inicial)
        self.content_layout.addWidget(self.modulo_corte)
        self.modulo_corte.hide()

        # Organización en el Layout
        self.content_layout.addWidget(self.modulo_pendientes)
        self.content_layout.addWidget(self.modulo_cobradas)
        
        self.modulo_cobradas.hide()
        self.sidebar.resaltar_boton("Órdenes Pendientes")

        main_layout.addWidget(content_area)

    def cambiar_vista(self, vista):
        self.sidebar.resaltar_boton(vista)
        self.modulo_pendientes.hide()
        self.modulo_cobradas.hide()
        self.modulo_corte.hide()

        if vista == "Órdenes Pendientes":
            self.modulo_pendientes.show()
            self.modulo_pendientes.cargar_datos_del_dia()
        elif vista == "Ventas Cobradas":
            self.modulo_cobradas.show()
            self.modulo_cobradas.cargar_datos_del_dia()
        elif vista == "Corte de Caja":
            self.modulo_corte.show()
            self.modulo_corte.cargar_totales()

    def abrir_ventana_cobro(self, folio):
        dialog = VentanaCobro(folio, self.ws, self.user_data, self, modo_solo_lectura=False)
        if dialog.exec():
            self.modulo_pendientes.cargar_datos_del_dia()
            self.modulo_cobradas.cargar_datos_del_dia()

    def reimprimir_ticket(self, folio):
        """Busca los datos históricos de una venta cobrada y vuelve a disparar el ticket"""
        import os, sys
        from backend.generador_pdf import GeneradorPDF
        try:
            # Consultamos los datos de la venta y de la auditoría de su cobro
            query = """
                SELECT v.id_venta, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), c.nombre_completo, v.cliente_temporal, v.total,
                       co.monto_recibido, co.cambio, co.metodo_pago, emp.nombre_completo as cajero
                FROM orden_venta v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                LEFT JOIN cobro_venta co ON v.id_venta = co.id_venta
                LEFT JOIN empleados emp ON co.id_cajero = emp.id_empleado
                WHERE v.folio = %s
            """
            res = self.db.fetch_one(query, (folio,))
            if not res:
                AlertaCustom.show_error(self, "Error", f"No se encontraron registros de cobro para el folio {folio}")
                return
            
            id_venta, fecha, hora, cliente, cte_temp, total, rec, cam, met, cajero = res
            nombre_cliente = f"{cliente} ({cte_temp})" if cte_temp and cte_temp != 'MOSTRADOR' else cliente

            # Traemos las partidas del detalle
            query_prod = """
                SELECT p.codigo, p.nombre, d.cantidad, d.descuento, d.precio_unitario, d.subtotal
                FROM detalle_venta d
                JOIN productos p ON d.id_producto = p.id_producto
                WHERE d.id_venta = %s
            """
            productos_db = self.db.fetch_all(query_prod, (id_venta,))
            
            datos_ticket = {
                "folio": folio,
                "fecha": str(fecha),
                "hora": hora,
                "cajero": cajero if cajero else "Caja General",
                "cliente": nombre_cliente,
                "productos": productos_db,
                "total": float(total),
                "recibido": float(rec) if rec else 0.0,
                "cambio": float(cam) if cam else 0.0,
                "metodo": met if met else "Efectivo"
            }

            carpeta_tickets = os.path.join(os.getcwd(), "tickets")
            os.makedirs(carpeta_tickets, exist_ok=True)
            ruta_salida = os.path.join(carpeta_tickets, f"Ticket_{folio}_Reimpresion.pdf")

            pdf = GeneradorPDF()
            pdf.generar_ticket_venta(datos_ticket, ruta_salida)

            # Abrimos el visor nativo de inmediato
            if sys.platform == "win32":
                os.startfile(ruta_salida)
            else:
                import subprocess
                subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", ruta_salida])
                
            AlertaCustom.show_success(self, "Reimpresión", f"Ticket {folio} enviado a vista de impresión.")
        except Exception as e:
            AlertaCustom.show_error(self, "Error", f"No se pudo regenerar el ticket: {e}")

    def ver_detalle_cobrada(self, folio):
        dialog = VentanaCobro(folio, self.ws, self.user_data, self, modo_solo_lectura=True)
        dialog.exec()

    def al_recibir_notificacion(self, mensaje):
        datos = json.loads(mensaje)
        
        if datos["tipo"] in ["NUEVA_ORDEN", "ORDEN_COBRADA"]:
            # El WebSocket avisa que hay un cambio y recargamos directamente de la BD
            self.modulo_pendientes.cargar_datos_del_dia()
            self.modulo_cobradas.cargar_datos_del_dia()
            
    def verificar_apertura(self):
        query = "SELECT id_corte, fondo_inicial FROM cortes_caja WHERE id_cajero = %s AND estatus = 'Abierta'"
        res = self.db.fetch_one(query, (self.user_data['id'],))
        if self.user_data.get('rol') == 'Administrador': return
        
        if res:
            self.id_corte_activo, self.fondo_inicial = res[0], float(res[1])
        else:
            modal = AperturaCajaModal(self.user_data['id'], self)
            if modal.exec():
                self.id_corte_activo = modal.id_corte_generado
                self.fondo_inicial = modal.fondo_ingresado
            else:
                self.close()
    
    def abrir_configuracion(self):
        modal = ConfiguracionHardwareModal(self)
        modal.exec()

# ==========================================
# CLASE: CONFIGURACIÓN DE HARDWARE (CAJA)
# ==========================================
from PyQt6.QtWidgets import QDialog, QComboBox, QFormLayout, QLabel, QPushButton
from PyQt6.QtCore import QSettings

class ConfiguracionHardwareModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("Ferrosoft", "HardwareCaja")
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Configuración de Dispositivos (Caja)")
        self.setFixedSize(450, 300)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # Escanear Impresoras
        try:
            from PyQt6.QtPrintSupport import QPrinterInfo
            impresoras = [p.printerName() for p in QPrinterInfo.availablePrinters()]
        except:
            impresoras = ["EPSON TM-T20III", "Xprinter 80mm", "Microsoft Print to PDF"]
        
        if not impresoras: impresoras = ["Ninguna impresora detectada"]

        # Escanear Puertos (Cajón de dinero)
        puertos = ["USB (Conectado a Impresora)", "COM1", "COM2", "COM3"]
        try:
            import serial.tools.list_ports
            puertos_reales = [p.device for p in serial.tools.list_ports.comports()]
            if puertos_reales: puertos = ["USB (Conectado a Impresora)"] + puertos_reales
        except:
            pass

        # Formulario UI
        lbl_titulo = QLabel("⚙️ Hardware Local")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b;")
        layout.addWidget(lbl_titulo)
        layout.addSpacing(10)

        formulario = QFormLayout()
        
        self.combo_impresora = QComboBox()
        self.combo_impresora.addItems(impresoras)
        self.combo_impresora.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px;")
        
        # Recuperar la impresora guardada si existe
        impresora_guardada = self.settings.value("impresora_tickets", "")
        if impresora_guardada in impresoras:
            self.combo_impresora.setCurrentText(impresora_guardada)

        self.combo_cajon = QComboBox()
        self.combo_cajon.addItems(puertos)
        self.combo_cajon.setStyleSheet("padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px;")
        
        cajon_guardado = self.settings.value("puerto_cajon", "")
        if cajon_guardado in puertos:
            self.combo_cajon.setCurrentText(cajon_guardado)

        formulario.addRow("<b>Impresora de Tickets:</b>", self.combo_impresora)
        formulario.addRow("<b>Puerto Cajón de Dinero:</b>", self.combo_cajon)
        layout.addLayout(formulario)
        layout.addStretch()

        # Botones
        botones_ly = QHBoxLayout()
        btn_probar = QPushButton("🧪 Probar Cajón")
        btn_probar.setStyleSheet("background-color: #64748b; color: white; padding: 10px; border-radius: 5px;")
        btn_probar.clicked.connect(self.probar_cajon)

        btn_guardar = QPushButton("💾 Guardar Configuración")
        btn_guardar.setStyleSheet("background-color: #10b981; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        btn_guardar.clicked.connect(self.guardar_config)

        botones_ly.addWidget(btn_probar)
        botones_ly.addWidget(btn_guardar)
        layout.addLayout(botones_ly)

    def probar_cajon(self):
        from frontend.components.alertas import AlertaCustom
        AlertaCustom.show_info(self, "Prueba Hardware", f"Enviando pulso de apertura al puerto {self.combo_cajon.currentText()}...")

    def guardar_config(self):
        from frontend.components.alertas import AlertaCustom
        self.settings.setValue("impresora_tickets", self.combo_impresora.currentText())
        self.settings.setValue("puerto_cajon", self.combo_cajon.currentText())
        AlertaCustom.show_success(self, "Hardware Configurado", "Los dispositivos locales se vincularon con éxito.")
        self.accept()