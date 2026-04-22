# frontend/views/crear_orden.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWebSockets import QWebSocket
import json
import datetime

from frontend.components.elementos_ui import FormInput, PrimaryButton, DataTable
from frontend.components.carrito_manejador import CarritoManager
from frontend.components.alertas import AlertaCustom
from frontend.components.buscador import GenericSearchModal
from backend.bd_conexion import DatabaseConnection

class CreateOrderWindow(QDialog):
    def __init__(self, user_data, parent=None, folio_editar=None):
        super().__init__(parent)
        self.user_data = user_data
        self.folio_editar = folio_editar
        self.id_venta_actual = None
        self.modo_edicion_activo = False
        self.is_venta_especial = False
        self.db = DatabaseConnection()
        
        self.ws_cliente = QWebSocket()
        self.ws_cliente.open(QUrl("ws://localhost:8765"))
        
        self.init_ui()
        self.setup_shortcuts()
        
        if self.folio_editar:
            self.cargar_datos_para_edicion()

    def init_ui(self):
        titulo = f"VISTA PREVIA ORDEN: {self.folio_editar}" if self.folio_editar else "Nueva Orden de Venta"
        self.setWindowTitle(f"{titulo} - El Tornillo Feliz")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setStyleSheet("background-color: #ffffff;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # ==========================================
        # 1. TOP SECTION (Cliente, Folio y Stock)
        # ==========================================
        top_layout = QHBoxLayout()
        
        info_grid = QGridLayout()
        info_grid.addWidget(QLabel("<b>CLIENTE</b>"), 0, 0)
        self.input_cliente = QLineEdit("Venta mostrador")
        self.input_cliente.setReadOnly(True)
        self.input_cliente.setStyleSheet("background-color: #ecf0f1; padding: 5px;")
        info_grid.addWidget(self.input_cliente, 0, 1)

        info_grid.addWidget(QLabel("<b>FOLIO</b>"), 0, 2)
        self.input_folio = QLineEdit(self.folio_editar if self.folio_editar else "Generando...")
        self.input_folio.setReadOnly(True)
        self.input_folio.setStyleSheet("background-color: #ecf0f1;")
        info_grid.addWidget(self.input_folio, 0, 3)

        self.btn_especial = QPushButton("venta especial")
        self.btn_especial.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 5px;")
        self.btn_especial.clicked.connect(self.toggle_venta_especial)
        info_grid.addWidget(self.btn_especial, 1, 2, 1, 2) 

        top_layout.addLayout(info_grid)
        top_layout.addStretch()

        # Tabla de Consulta de Stock
        stock_layout = QVBoxLayout()
        lbl_stock = QLabel("<b>CONSULTA STOCK</b>")
        lbl_stock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stock_layout.addWidget(lbl_stock)
        
        self.tabla_stock = DataTable(["ALMACEN", "CANTIDAD"])
        self.tabla_stock.setFixedSize(300, 100)
        stock_layout.addWidget(self.tabla_stock)
        top_layout.addLayout(stock_layout)
        
        main_layout.addLayout(top_layout)

        # ==========================================
        # 2. BUSCADOR
        # ==========================================
        self.search_input = FormInput("F2 - Buscar producto por nombre o codigo...")
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        main_layout.addWidget(self.search_input)

        # ==========================================
        # 3. CARRITO MANAGER
        # ==========================================
        self.carrito_manager = CarritoManager()
        # Conectamos el clic de la tabla del carrito para que consulte el stock arriba
        self.carrito_manager.tabla.itemSelectionChanged.connect(self.consultar_stock_seleccion)
        main_layout.addWidget(self.carrito_manager)

        # ==========================================
        # 4. FOOTER Y BOTONES
        # ==========================================
        footer = QHBoxLayout()
        btn_cancelar = PrimaryButton("CANCELAR")
        btn_cancelar.setStyleSheet("background-color: #e74c3c; padding: 10px 20px;")
        btn_cancelar.clicked.connect(self.reject)
        
        self.btn_editar = PrimaryButton("✏️ EDITAR ORDEN")
        self.btn_editar.setStyleSheet("background-color: #f39c12; padding: 10px 20px;")
        self.btn_editar.clicked.connect(self.desbloquear_edicion)
        self.btn_editar.hide()

        self.btn_enviar = PrimaryButton("ENVIAR A CAJA F3")
        self.btn_enviar.setStyleSheet("padding: 10px 20px;")
        self.btn_enviar.clicked.connect(self.generate_order)

        footer.addWidget(btn_cancelar)
        footer.addStretch()
        footer.addWidget(self.btn_editar)
        footer.addWidget(self.btn_enviar)
        main_layout.addLayout(footer)

    def setup_shortcuts(self):
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        self.shortcut_f2.activated.connect(self.search_input.setFocus)
        self.shortcut_f3 = QShortcut(QKeySequence(Qt.Key.Key_F3), self)
        self.shortcut_f3.activated.connect(self.generate_order)

    def toggle_venta_especial(self):
        self.is_venta_especial = not self.is_venta_especial
        if self.is_venta_especial:
            self.input_cliente.setReadOnly(False)
            self.input_cliente.setStyleSheet("background-color: #ffffff; padding: 5px;")
            self.input_cliente.setText("")
            self.input_cliente.setPlaceholderText("Buscar cliente...")
            self.input_cliente.setFocus()
            self.btn_especial.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 5px;")
            self.btn_especial.setText("venta mostrador")
            self.abrir_buscador_clientes()
        else:
            self.input_cliente.setReadOnly(True)
            self.input_cliente.setStyleSheet("background-color: #ecf0f1; padding: 5px;")
            self.input_cliente.setText("Venta mostrador")
            self.btn_especial.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 5px;")
            self.btn_especial.setText("venta especial")

    def abrir_buscador_clientes(self):
        def query_cl(b):
            q = "SELECT rfc, nombre_completo, id_cliente FROM clientes WHERE estatus = TRUE AND (rfc ILIKE %s OR nombre_completo ILIKE %s)"
            return self.db.fetch_all(q, (f"%{b}%", f"%{b}%"))
        
        modal = GenericSearchModal("Buscar Cliente", "RFC o nombre...", ["RFC", "NOMBRE", "ID"], query_cl, self)
        if modal.exec():
            self.input_cliente.setText(modal.selected_data[1])

    def cargar_datos_para_edicion(self):
        try:
            query = """
                SELECT v.id_venta, c.nombre_completo, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), v.estatus
                FROM orden_venta v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                WHERE v.folio = %s
            """
            res = self.db.fetch_one(query, (self.folio_editar,))
            if not res: return
            
            self.id_venta_actual, cliente, fecha, hora, estatus = res
            self.input_cliente.setText(cliente)

            query_det = """
                SELECT p.id_producto, p.codigo, p.nombre, d.cantidad, d.descuento, d.precio_unitario, d.subtotal
                FROM detalle_venta d
                JOIN productos p ON d.id_producto = p.id_producto
                WHERE d.id_venta = %s
            """
            detalles_db = self.db.fetch_all(query_det, (self.id_venta_actual,))
            
            carrito_lista = []
            for d in detalles_db:
                carrito_lista.append({
                    "id": d[0], "codigo": d[1], "nombre": d[2],
                    "cant": float(d[3]), "desc": float(d[4]),
                    "precio": float(d[5]), "subtotal": float(d[6])
                })
            
            self.carrito_manager.cargar_carrito_existente(carrito_lista)
            
            # Bloqueo
            self.search_input.setEnabled(False)
            self.btn_enviar.setEnabled(False)
            self.btn_especial.setEnabled(False)
            self.carrito_manager.bloquear_edicion()
            
            if estatus != 'Cobrada':
                self.btn_editar.show()
            else:
                self.btn_enviar.setText("ORDEN COBRADA")
                
        except Exception as e:
            AlertaCustom.show_error(self, "Error de Carga", str(e))

    def desbloquear_edicion(self):
        self.modo_edicion_activo = True
        self.setWindowTitle(f"EDITANDO ORDEN: {self.folio_editar}")
        self.search_input.setEnabled(True)
        self.btn_enviar.setEnabled(True)
        self.btn_enviar.setText("GUARDAR CAMBIOS F3")
        self.btn_enviar.setStyleSheet("background-color: #27ae60; padding: 10px 20px;")
        self.btn_editar.hide()
        self.carrito_manager.desbloquear_edicion()
        AlertaCustom.show_info(self, "Edición Habilitada", "Ya puedes modificar la orden.")

    def generate_order(self):
        productos, total = self.carrito_manager.obtener_datos()
        if not productos:
            AlertaCustom.show_error(self, "Carrito Vacío", "No hay productos en la orden.")
            return

        try:
            now = datetime.datetime.now()
            hora_limpia = now.strftime('%H:%M')

            if self.folio_editar and self.modo_edicion_activo:
                self.db.execute_query("UPDATE orden_venta SET total = %s, hora = %s WHERE id_venta = %s", 
                                      (total, hora_limpia, self.id_venta_actual))
                self.db.execute_query("DELETE FROM detalle_venta WHERE id_venta = %s", (self.id_venta_actual,))
                id_final = self.id_venta_actual
                folio_final = self.folio_editar
            else:
                folio_final = f"OV-{now.strftime('%Y%m%d%H%M%S')}"
                query_ins = """
                    INSERT INTO orden_venta (folio, id_vendedor, fecha, hora, id_cliente, total, estatus) 
                    VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente') RETURNING id_venta
                """
                id_final = self.db.fetch_one(query_ins, (folio_final, self.user_data['id'], now.date(), hora_limpia, 1, total))[0]

            query_det = "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento, subtotal) VALUES (%s, %s, %s, %s, %s, %s)"
            for p in productos:
                self.db.execute_query(query_det, (id_final, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

            self.ws_cliente.sendTextMessage(json.dumps({"tipo": "NUEVA_ORDEN", "folio": folio_final, "vendedor": self.user_data['nombre'], "total": total}))
            AlertaCustom.show_success(self, "Éxito", f"Orden {folio_final} generada y enviada a caja.")
            self.accept()
            
        except Exception as e:
            AlertaCustom.show_error(self, "Error al Guardar", str(e))

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
            q = "SELECT codigo, nombre, precio_venta, id_producto FROM productos WHERE estatus=TRUE AND (codigo ILIKE %s OR nombre ILIKE %s) LIMIT 50"
            return self.db.fetch_all(q, (f"%{t}%", f"%{t}%"))

        modal = GenericSearchModal("Buscar Producto", "Escribe para buscar...", ["CODIGO", "NOMBRE", "PRECIO", "ID"], query_func, self)
        if texto: modal.search_input.setText(texto)
        if modal.exec():
            self.agregar_por_codigo_directo(modal.selected_data[0])

    def consultar_stock_seleccion(self):
        """Consulta el stock del producto que seleccionaste en el carrito"""
        current_row = self.carrito_manager.tabla.currentRow()
        if current_row < 0: return

        # Obtenemos el ID del producto desde la lista interna del manager
        id_prod = self.carrito_manager.productos[current_row]['id']

        query_stock = """
            SELECT a.nombre, i.cantidad_existente 
            FROM inventario_almacen i
            JOIN almacenes a ON i.id_almacen = a.id_almacen
            WHERE i.id_producto = %s
        """
        stocks = self.db.fetch_all(query_stock, (id_prod,))
        
        self.tabla_stock.setRowCount(len(stocks))
        from PyQt6.QtWidgets import QTableWidgetItem
        for i, (almacen, cantidad) in enumerate(stocks):
            self.tabla_stock.setItem(i, 0, QTableWidgetItem(almacen))
            self.tabla_stock.setItem(i, 1, QTableWidgetItem(str(cantidad)))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
        else:
            super().keyPressEvent(event)