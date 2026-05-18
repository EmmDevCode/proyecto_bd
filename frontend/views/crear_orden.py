# frontend/views/crear_orden.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QPushButton, QFrame, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
import datetime
import qtawesome as qta

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
        self.id_cliente_seleccionado = 1
        self.db = DatabaseConnection()
        
        self.init_ui()
        self.setup_shortcuts()
        
        if self.folio_editar:
            self.cargar_datos_para_edicion()

    def init_ui(self):
        titulo = f"VISTA PREVIA ORDEN: {self.folio_editar}" if self.folio_editar else "Nueva Orden de Venta"
        self.setWindowTitle(f"{titulo} - El Tornillo Feliz")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setStyleSheet("background-color: #f1f5f9;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Función auxiliar para crear tarjetas
        def crear_tarjeta():
            tarjeta = QFrame()
            tarjeta.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border-radius: 12px;
                    border: 1px solid #e2e8f0;
                }
            """)
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(Qt.GlobalColor.lightGray)
            shadow.setOffset(0, 2)
            tarjeta.setGraphicsEffect(shadow)
            return tarjeta

      
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        
        # Tarjeta Info Cliente
        card_info = crear_tarjeta()
        info_layout = QVBoxLayout(card_info)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(15)
        
        titulo_info = QLabel("DATOS DE LA ORDEN")
        titulo_info.setStyleSheet("font-size: 11pt; font-weight: 800; color: #475569; border: none;")
        info_layout.addWidget(titulo_info)
        
        info_grid = QGridLayout()
        info_grid.setSpacing(10)
        
        lbl_cliente = QLabel("CLIENTE:")
        lbl_cliente.setStyleSheet("font-weight: bold; color: #64748b; border: none;")
        info_grid.addWidget(lbl_cliente, 0, 0)
        self.input_cliente = QLineEdit("Venta mostrador")
        self.input_cliente.setReadOnly(True)
        self.input_cliente.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; color: #334155; font-weight: bold;")
        info_grid.addWidget(self.input_cliente, 0, 1)

        lbl_folio = QLabel("FOLIO:")
        lbl_folio.setStyleSheet("font-weight: bold; color: #64748b; border: none;")
        info_grid.addWidget(lbl_folio, 0, 2)
        self.input_folio = QLineEdit(self.folio_editar if self.folio_editar else "Generando...")
        self.input_folio.setReadOnly(True)
        self.input_folio.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; color: #334155; font-weight: bold;")
        info_grid.addWidget(self.input_folio, 0, 3)

        self.btn_especial = QPushButton(" Venta Especial ")
        self.btn_especial.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_especial.setStyleSheet("""
            QPushButton { background-color: #ef4444; color: white; border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.btn_especial.clicked.connect(self.toggle_venta_especial)
        info_grid.addWidget(self.btn_especial, 1, 2, 1, 2) 

        info_layout.addLayout(info_grid)
        top_layout.addWidget(card_info, stretch=2)

        # Tarjeta Consulta de Stock
        card_stock = crear_tarjeta()
        stock_layout = QVBoxLayout(card_stock)
        stock_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_stock = QLabel("CONSULTA DE STOCK")
        lbl_stock.setStyleSheet("font-size: 11pt; font-weight: 800; color: #475569; border: none;")
        stock_layout.addWidget(lbl_stock)
        
        self.tabla_stock = DataTable(["ALMACÉN", "CANTIDAD"])
        self.tabla_stock.setFixedSize(300, 90)
        self.tabla_stock.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 4px;")
        stock_layout.addWidget(self.tabla_stock)
        top_layout.addWidget(card_stock, stretch=1)
        
        main_layout.addLayout(top_layout, stretch=1)

      
        card_carrito = crear_tarjeta()
        carrito_layout = QVBoxLayout(card_carrito)
        carrito_layout.setContentsMargins(20, 20, 20, 20)
        carrito_layout.setSpacing(15)
        
        lbl_carrito = QLabel("DETALLE DE LA ORDEN")
        lbl_carrito.setStyleSheet("font-size: 11pt; font-weight: 800; color: #475569; border: none;")
        carrito_layout.addWidget(lbl_carrito)
        
        self.search_input = FormInput("F2 - Buscar producto por nombre o codigo...")
        self.search_input.setStyleSheet("""
            QLineEdit { border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 12pt; background-color: #f8fafc; }
            QLineEdit:focus { border: 2px solid #3b82f6; background-color: #ffffff; }
        """)
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        carrito_layout.addWidget(self.search_input)

        self.carrito_manager = CarritoManager()
        self.carrito_manager.setStyleSheet("border: none;")
        # Conectamos el clic de la tabla del carrito para que consulte el stock arriba
        self.carrito_manager.tabla.itemSelectionChanged.connect(self.consultar_stock_seleccion)
        carrito_layout.addWidget(self.carrito_manager)
        
        main_layout.addWidget(card_carrito, stretch=5)

    
        card_footer = crear_tarjeta()
        card_footer.setStyleSheet("""
            QFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; border-top: 4px solid #3b82f6; }
        """)
        footer = QHBoxLayout(card_footer)
        footer.setContentsMargins(20, 15, 20, 15)
        
        btn_cancelar = QPushButton("  CANCELAR")
        btn_cancelar.setIcon(qta.icon('fa5s.times', color='white'))
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton { background-color: #ef4444; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 10pt; }
            QPushButton:hover { background-color: #dc2626; }
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        self.btn_editar = QPushButton("  EDITAR ORDEN")
        self.btn_editar.setIcon(qta.icon('fa5s.edit', color='white'))
        self.btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editar.setStyleSheet("""
            QPushButton { background-color: #f59e0b; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 10pt; }
            QPushButton:hover { background-color: #d97706; }
        """)
        self.btn_editar.clicked.connect(self.desbloquear_edicion)
        self.btn_editar.hide()

        self.btn_enviar = QPushButton("  ENVIAR A CAJA (F3)")
        self.btn_enviar.setIcon(qta.icon('fa5s.paper-plane', color='white'))
        self.btn_enviar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enviar.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: 800; font-size: 11pt; }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
        """)
        self.btn_enviar.clicked.connect(self.generate_order)

        footer.addWidget(btn_cancelar)
        footer.addStretch() 
        
        footer.addWidget(self.carrito_manager.lbl_total, alignment=Qt.AlignmentFlag.AlignVCenter)
        footer.addSpacing(20) 
        
        footer.addWidget(self.btn_editar)
        footer.addWidget(self.btn_enviar)
        main_layout.addWidget(card_footer)

    def setup_shortcuts(self):
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        self.shortcut_f2.activated.connect(self.search_input.setFocus)
        self.shortcut_f3 = QShortcut(QKeySequence(Qt.Key.Key_F3), self)
        self.shortcut_f3.activated.connect(self.generate_order)

    def toggle_venta_especial(self):
        self.is_venta_especial = not self.is_venta_especial
        if self.is_venta_especial:
            self.input_cliente.setReadOnly(False)
            self.input_cliente.setStyleSheet("background-color: #ffffff; border: 2px solid #3b82f6; border-radius: 6px; padding: 8px; color: #334155; font-weight: bold;")
            self.input_cliente.setText("")
            self.input_cliente.setPlaceholderText("Buscar cliente...")
            self.input_cliente.setFocus()
            self.btn_especial.setStyleSheet("QPushButton { background-color: #10b981; color: white; border-radius: 6px; padding: 8px; font-weight: bold; } QPushButton:hover { background-color: #059669; }")
            self.btn_especial.setText("Venta Mostrador")
            self.abrir_buscador_clientes()
        else:
            self.id_cliente_seleccionado = 1
            self.input_cliente.setReadOnly(True)
            self.input_cliente.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; color: #334155; font-weight: bold;")
            self.input_cliente.setText("Venta mostrador")
            self.btn_especial.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border-radius: 6px; padding: 8px; font-weight: bold; } QPushButton:hover { background-color: #dc2626; }")
            self.btn_especial.setText("Venta Especial")

    def abrir_buscador_clientes(self):
        def query_cl(b):
            q = "SELECT rfc, nombre_completo, id_cliente FROM clientes WHERE estatus = TRUE AND (rfc ILIKE %s OR nombre_completo ILIKE %s)"
            return self.db.fetch_all(q, (f"%{b}%", f"%{b}%"))
        
        modal = GenericSearchModal("Buscar Cliente", "RFC o nombre...", ["RFC", "NOMBRE", "ID"], query_cl, self)
        if modal.exec():
            self.input_cliente.setText(modal.selected_data[1])
            self.id_cliente_seleccionado = modal.selected_data[2]
        else:
            self.toggle_venta_especial()

    def cargar_datos_para_edicion(self):
        try:
            query = """
                SELECT v.id_venta, c.nombre_completo, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), v.estatus, v.cliente_temporal, v.id_cliente
                FROM orden_venta v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                WHERE v.folio = %s
            """
            res = self.db.fetch_one(query, (self.folio_editar,))
            if not res: return
            
            self.id_venta_actual, cliente, fecha, hora, estatus, cte_temp, id_cliente = res
            self.id_cliente_seleccionado = id_cliente
            
            if cte_temp and cte_temp != 'MOSTRADOR':
                self.input_cliente.setText(f"{cliente} ({cte_temp})")
            else:
                self.input_cliente.setText(cliente)

           
            query_det = """
                SELECT p.id_producto, p.codigo, p.nombre, p.unidad_medida, d.cantidad, d.descuento, d.precio_unitario, d.subtotal
                FROM detalle_venta d
                JOIN productos p ON d.id_producto = p.id_producto
                WHERE d.id_venta = %s
            """
            detalles_db = self.db.fetch_all(query_det, (self.id_venta_actual,))
            
            carrito_lista = []
            for d in detalles_db:
                carrito_lista.append({
                    "id": d[0], "codigo": d[1], "nombre": d[2], "unidad": d[3], 
                    "cant": float(d[4]), "desc": float(d[5]),
                    "precio": float(d[6]), "subtotal": float(d[7])
                })
            
            self.carrito_manager.cargar_carrito_existente(carrito_lista)
            
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
        self.btn_enviar.setText("  GUARDAR CAMBIOS (F3)")
        self.btn_enviar.setStyleSheet("QPushButton { background-color: #10b981; color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: 800; font-size: 11pt; } QPushButton:hover { background-color: #059669; }")
        self.btn_editar.hide()
        self.carrito_manager.desbloquear_edicion()
        AlertaCustom.show_info(self, "Edición Habilitada", "Ya puedes modificar la orden.")

    def generate_order(self):
        productos, total = self.carrito_manager.obtener_datos()
        if not productos:
            AlertaCustom.show_error(self, "Carrito Vacío", "No hay productos en la orden.")
            return

        nombre_ticket = ""
        if self.id_cliente_seleccionado == 1 and not self.modo_edicion_activo: 
            modal = NombreTemporalModal(self)
            if modal.exec():
                texto = modal.nombre_capturado
                if texto.strip():
                    nombre_ticket = texto.strip().upper()
                else:
                    nombre_ticket = "MOSTRADOR"
            else:
                nombre_ticket = "MOSTRADOR"
        else:
            nombre_ticket = "MOSTRADOR"

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
                    INSERT INTO orden_venta (folio, id_vendedor, fecha, hora, id_cliente, cliente_temporal, total, estatus) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pendiente') RETURNING id_venta
                """
                id_final = self.db.fetch_one(query_ins, (folio_final, self.user_data['id'], now.date(), hora_limpia, self.id_cliente_seleccionado, nombre_ticket, total))[0]

            query_det = "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento, subtotal) VALUES (%s, %s, %s, %s, %s, %s)"
            for p in productos:
                self.db.execute_query(query_det, (id_final, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

           
            self.folio_generado = folio_final
            
            AlertaCustom.show_success(self, "Éxito", f"Orden {folio_final} enviada a caja.\n\nCliente/Seña: {nombre_ticket}")
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
    
        query = "SELECT id_producto, codigo, nombre, unidad_medida, precio_venta FROM productos WHERE codigo = %s AND estatus = TRUE"
        p = self.db.fetch_one(query, (codigo,))
        if p:
            self.carrito_manager.agregar_producto(p[0], p[1], p[2], p[3], p[4])
        else:
            AlertaCustom.show_error(self, "No Encontrado", f"El código {codigo} no existe.")

    def abrir_buscador_avanzado(self, texto):
        def query_func(t):
            
            q = "SELECT codigo, nombre, unidad_medida, precio_venta, id_producto FROM productos WHERE estatus=TRUE AND (codigo ILIKE %s OR nombre ILIKE %s) LIMIT 50"
            return self.db.fetch_all(q, (f"%{t}%", f"%{t}%"))

        modal = GenericSearchModal("Buscar Producto", "Escribe para buscar...", ["CODIGO", "NOMBRE", "UNIDAD", "PRECIO", "ID"], query_func, self)
        if texto: modal.search_input.setText(texto)
        if modal.exec():
            self.agregar_por_codigo_directo(modal.selected_data[0])

    def consultar_stock_seleccion(self):
        current_row = self.carrito_manager.tabla.currentRow()
        if current_row < 0: return

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

class NombreTemporalModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nombre_capturado = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Identificar Cliente")
        self.setFixedWidth(400)
        self.setStyleSheet("background-color: #ffffff; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Icono + Título
        header = QHBoxLayout()
        icono = QLabel()
        icono.setPixmap(qta.icon('fa5s.user-tag', color='#3b82f6').pixmap(32, 32))
        
        lbl_titulo = QLabel("Identificar Cliente")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a;")
        
        header.addWidget(icono)
        header.addWidget(lbl_titulo)
        header.addStretch()
        layout.addLayout(header)
        
        # Subtítulo
        lbl_sub = QLabel("Nombre del cliente o seña particular para su ticket:\n(Opcional, presiona Enter para omitir)")
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b;")
        layout.addWidget(lbl_sub)
        
        # Input
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Joven gorra roja, Doña María...")
        self.input_nombre.setStyleSheet("""
            QLineEdit { border: 2px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 14px; background-color: #f8fafc; color: #1e293b; }
            QLineEdit:focus { border: 2px solid #3b82f6; background-color: #ffffff; }
        """)
        self.input_nombre.returnPressed.connect(self.aceptar)
        layout.addWidget(self.input_nombre)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_omitir = QPushButton("  Omitir")
        btn_omitir.setIcon(qta.icon('fa5s.forward', color='#64748b'))
        btn_omitir.setStyleSheet("""
            QPushButton { background-color: transparent; color: #64748b; padding: 10px 20px; font-weight: bold; border: 2px solid #e2e8f0; border-radius: 8px; }
            QPushButton:hover { background-color: #f1f5f9; color: #334155; border: 2px solid #cbd5e1; }
        """)
        btn_omitir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_omitir.clicked.connect(self.reject)
        
        btn_guardar = QPushButton("  Continuar")
        btn_guardar.setIcon(qta.icon('fa5s.check', color='white'))
        btn_guardar.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 12px 24px; border-radius: 8px; border: none;")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.clicked.connect(self.aceptar)
        
        btn_layout.addWidget(btn_omitir)
        btn_layout.addWidget(btn_guardar)
        layout.addLayout(btn_layout)

    def aceptar(self):
        self.nombre_capturado = self.input_nombre.text().strip()
        self.accept()