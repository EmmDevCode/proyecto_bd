# frontend/views/crear_cotizacion.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWebSockets import QWebSocket
import json
import datetime

# Componentes reutilizables del proyecto
from frontend.components.elementos_ui import FormInput, PrimaryButton
from frontend.components.carrito_manejador import CarritoManager
from frontend.components.alertas import AlertaCustom
from frontend.components.buscador import GenericSearchModal
from backend.bd_conexion import DatabaseConnection

class CreateQuotationWindow(QDialog):
    def __init__(self, user_data, parent=None, folio_editar=None):
        super().__init__(parent)
        self.user_data = user_data
        self.folio_editar = folio_editar
        self.id_cot_actual = None
        self.modo_edicion_activo = False
        self.db = DatabaseConnection()
        
        # Conexión WebSocket para notificar a otros módulos
        self.ws_cliente = QWebSocket()
        self.ws_cliente.open(QUrl("ws://localhost:8765"))
        
        self.init_ui()
        self.setup_shortcuts()
        
        # Si recibimos un folio, cargamos los datos en modo vista previa
        if self.folio_editar:
            self.cargar_datos_para_edicion()

    def init_ui(self):
        # Título dinámico según la acción
        if self.folio_editar:
            self.setWindowTitle(f"VISTA PREVIA COTIZACIÓN: {self.folio_editar}")
        else:
            self.setWindowTitle("Nueva Cotización - El Tornillo Feliz")
            
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setStyleSheet("background-color: #ffffff;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        # ==========================================
        # 1. ENCABEZADO (Info General)
        # ==========================================
        header_grid = QGridLayout()
        
        header_grid.addWidget(QLabel("<b>CLIENTE:</b>"), 0, 0)
        self.input_cliente = QLineEdit("Venta mostrador")
        self.input_cliente.setReadOnly(True)
        self.input_cliente.setStyleSheet("background-color: #ecf0f1; padding: 8px; border-radius: 4px;")
        header_grid.addWidget(self.input_cliente, 0, 1)

        header_grid.addWidget(QLabel("<b>FOLIO:</b>"), 0, 2)
        self.input_folio = QLineEdit(self.folio_editar if self.folio_editar else "AUTO-GENERADO")
        self.input_folio.setReadOnly(True)
        self.input_folio.setStyleSheet("background-color: #ecf0f1; padding: 8px; border-radius: 4px;")
        header_grid.addWidget(self.input_folio, 0, 3)

        main_layout.addLayout(header_grid)

        # ==========================================
        # 2. BÚSQUEDA (Escáner y Teclado)
        # ==========================================
        self.search_input = FormInput("F2 - Escribe el nombre o código del producto para cotizar...")
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        main_layout.addWidget(self.search_input)

        # ==========================================
        # 3. EL CARRITO (Componente Reutilizable)
        # ==========================================
        self.carrito_manager = CarritoManager()
        main_layout.addWidget(self.carrito_manager)

        # ==========================================
        # 4. BOTONERA (Footer)
        # ==========================================
        footer_layout = QHBoxLayout()
        
        # Botón para cancelar
        btn_cancelar = PrimaryButton("CANCELAR")
        btn_cancelar.setStyleSheet("background-color: #e74c3c; padding: 10px 20px;")
        btn_cancelar.clicked.connect(self.reject)

        # Botón para habilitar edición (solo modo vista previa)
        self.btn_habilitar_edicion = PrimaryButton("✏️ EDITAR COTIZACIÓN")
        self.btn_habilitar_edicion.setStyleSheet("background-color: #f39c12; padding: 10px 20px;")
        self.btn_habilitar_edicion.clicked.connect(self.desbloquear_edicion)
        self.btn_habilitar_edicion.hide()

        # Botón para convertir cotización a orden de venta
        self.btn_convertir = PrimaryButton("💵 CONVERTIR A VENTA")
        self.btn_convertir.setStyleSheet("background-color: #8e44ad; padding: 10px 20px;")
        self.btn_convertir.clicked.connect(self.convertir_a_venta)
        self.btn_convertir.hide()

        # Botón principal de guardado
        self.btn_guardar = PrimaryButton("GUARDAR COTIZACIÓN")
        self.btn_guardar.setStyleSheet("background-color: #27ae60; padding: 10px 20px;")
        self.btn_guardar.clicked.connect(self.save_quotation)

        footer_layout.addWidget(btn_cancelar)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_convertir)
        footer_layout.addWidget(self.btn_habilitar_edicion)
        footer_layout.addWidget(self.btn_guardar)
        
        main_layout.addLayout(footer_layout)

    def setup_shortcuts(self):
        """Atajos rápidos"""
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        self.shortcut_f2.activated.connect(self.search_input.setFocus)

    def bloquear_interfaz(self):
        """Activa el modo de solo lectura"""
        self.search_input.setEnabled(False)
        self.btn_guardar.setEnabled(False)
        self.carrito_manager.bloquear_edicion()

    def desbloquear_edicion(self):
        """Habilita los controles para modificar"""
        self.modo_edicion_activo = True
        self.setWindowTitle(f"EDITANDO COTIZACIÓN: {self.folio_editar}")
        self.search_input.setEnabled(True)
        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText("GUARDAR CAMBIOS")
        self.btn_habilitar_edicion.hide()
        self.carrito_manager.desbloquear_edicion()
        AlertaCustom.show_info(self, "Edición Habilitada", "Ya puedes modificar los artículos de esta cotización.")

    def cargar_datos_para_edicion(self):
        """Recupera la cotización de la BD"""
        try:
            query = """
                SELECT v.id_cotizacion, c.nombre_completo, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), v.total
                FROM cotizaciones v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                WHERE v.folio = %s
            """
            res = self.db.fetch_one(query, (self.folio_editar,))
            if res:
                self.id_cot_actual, cliente, fecha, hora, total = res
                self.input_cliente.setText(cliente)
                
                # Cargar los productos asociados
                query_det = """
                    SELECT p.id_producto, p.codigo, p.nombre, d.cantidad, d.descuento, d.precio_unitario, d.subtotal
                    FROM detalle_cotizacion d
                    JOIN productos p ON d.id_producto = p.id_producto
                    WHERE d.id_cotizacion = %s
                """
                detalles_db = self.db.fetch_all(query_det, (self.id_cot_actual,))
                
                carrito_lista = []
                for d in detalles_db:
                    carrito_lista.append({
                        "id": d[0], "codigo": d[1], "nombre": d[2],
                        "cant": float(d[3]), "desc": float(d[4]),
                        "precio": float(d[5]), "subtotal": float(d[6])
                    })
                
                self.carrito_manager.cargar_carrito_existente(carrito_lista)
                self.bloquear_interfaz()
                self.btn_habilitar_edicion.show()
                self.btn_convertir.show()
        except Exception as e:
            AlertaCustom.show_error(self, "Error de Carga", f"No se pudo recuperar la cotización: {e}")

    def save_quotation(self):
        """Crea o actualiza la cotización en la BD"""
        productos, total = self.carrito_manager.obtener_datos()
        if not productos:
            AlertaCustom.show_error(self, "Carrito Vacío", "No hay artículos para cotizar.")
            return

        try:
            now = datetime.datetime.now()
            hora_limpia = now.strftime('%H:%M')

            if self.folio_editar and self.modo_edicion_activo:
                # Caso UPDATE
                self.db.execute_query("UPDATE cotizaciones SET total = %s, hora = %s WHERE id_cotizacion = %s", 
                                      (total, hora_limpia, self.id_cot_actual))
                self.db.execute_query("DELETE FROM detalle_cotizacion WHERE id_cotizacion = %s", (self.id_cot_actual,))
                id_final = self.id_cot_actual
                folio_final = self.folio_editar
            else:
                # Caso INSERT
                folio_final = f"COT-{now.strftime('%Y%m%d%H%M%S')}"
                query_ins = """
                    INSERT INTO cotizaciones (folio, id_vendedor, fecha, hora, id_cliente, total) 
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_cotizacion
                """
                id_final = self.db.fetch_one(query_ins, (folio_final, self.user_data['id'], now.date(), hora_limpia, 1, total))[0]

            # Insertar los productos en el detalle
            query_det = """
                INSERT INTO detalle_cotizacion (id_cotizacion, id_producto, cantidad, precio_unitario, descuento, subtotal) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            for p in productos:
                self.db.execute_query(query_det, (id_final, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

            # Notificar
            self.ws_cliente.sendTextMessage(json.dumps({"tipo": "NUEVA_COTIZACION", "folio": folio_final}))
            AlertaCustom.show_success(self, "Éxito", f"Cotización {folio_final} guardada correctamente.")
            self.accept()
            
        except Exception as e:
            AlertaCustom.show_error(self, "Error al Guardar", str(e))

    def convertir_a_venta(self):
        """Crea una orden de venta a partir de esta cotización"""
        if AlertaCustom.ask_confirm(self, "Convertir a Venta", "¿Deseas generar una Orden de Venta con estos productos?"):
            try:
                productos, total = self.carrito_manager.obtener_datos()
                now = datetime.datetime.now()
                folio_ov = f"OV-{now.strftime('%Y%m%d%H%M%S')}"
                
                # Insertar en orden_venta
                query_ov = """
                    INSERT INTO orden_venta (folio, id_vendedor, fecha, hora, id_cliente, total, estatus)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente') RETURNING id_venta
                """
                id_v = self.db.fetch_one(query_ov, (folio_ov, self.user_data['id'], now.date(), now.strftime('%H:%M'), 1, total))[0]
                
                # Insertar detalles en detalle_venta
                query_dv = """
                    INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                for p in productos:
                    self.db.execute_query(query_dv, (id_v, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

                self.ws_cliente.sendTextMessage(json.dumps({"tipo": "NUEVA_ORDEN", "folio": folio_ov}))
                AlertaCustom.show_success(self, "Venta Generada", f"Se creó la orden {folio_ov}. El cajero ya puede cobrarla.")
                self.accept()
            except Exception as e:
                AlertaCustom.show_error(self, "Error de Conversión", str(e))

    # --- Funciones de búsqueda (Igual que en ventas) ---
    def procesar_busqueda(self):
        texto = self.search_input.text().strip()
        if not texto: return
        if texto.isdigit():
            self.agregar_por_codigo_directo(texto)
        else:
            self.abrir_buscador_avanzado(texto)
        self.search_input.clear()

    def agregar_por_codigo_directo(self, codigo):
        query = "SELECT id_producto, codigo, nombre, precio_venta FROM productos WHERE codigo = %s AND estatus = TRUE"
        p = self.db.fetch_one(query, (codigo,))
        if p:
            self.carrito_manager.agregar_producto(p[0], p[1], p[2], p[3])
        else:
            AlertaCustom.show_error(self, "No Encontrado", f"El código {codigo} no existe.")

    def abrir_buscador_avanzado(self, texto):
        def query_func(t):
            q = "SELECT codigo, nombre, precio_venta, id_producto FROM productos WHERE estatus=T AND (codigo ILIKE %s OR nombre ILIKE %s) LIMIT 50"
            return self.db.fetch_all(q, (f"%{t}%", f"%{t}%"))

        modal = GenericSearchModal("Buscar Producto", "Escribe para buscar...", ["CODIGO", "NOMBRE", "PRECIO", "ID"], query_func, self)
        if texto: modal.search_input.setText(texto)
        if modal.exec():
            self.agregar_por_codigo_directo(modal.selected_data[0])