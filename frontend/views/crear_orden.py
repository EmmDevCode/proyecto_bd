# frontend/views/create_order_window.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidgetItem, QAbstractItemView, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut
from frontend.components.elementos_ui import FormInput, PrimaryButton, DataTable
from backend.bd_conexion import DatabaseConnection
import datetime
import json
from PyQt6.QtWebSockets import QWebSocket


from frontend.components.buscador import GenericSearchModal

class CreateOrderWindow(QDialog):
    def __init__(self, user_data, parent=None, folio_editar=None):
        super().__init__(parent)
        self.user_data = user_data
        self.db = DatabaseConnection()
        self.folio_editar = folio_editar
        self.id_venta_actual = None
        self.modo_edicion_activo = False
        self.carrito = [] 
        self.is_venta_especial = False
        self.ws_cliente = QWebSocket()
        self.ws_cliente.open(QUrl("ws://localhost:8765"))
        self.init_ui()
        self.setup_shortcuts()

        if self.folio_editar:
            self.cargar_datos_para_edicion()

    def init_ui(self):
        if self.folio_editar:
            self.setWindowTitle(f"VISTA PREVIA: {self.folio_editar} - El Tornillo Feliz")
        else:
            self.setWindowTitle("Nueva Orden de Venta - El Tornillo Feliz")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setStyleSheet("background-color: #ffffff;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # ==========================================
        # TOP SECTION: Info, Botones y Stock
        # ==========================================
        top_layout = QHBoxLayout()
        
        # Grid izquierdo (Cliente, Vendedor, Folio, Fecha)
        info_grid = QGridLayout()
        
        info_grid.addWidget(QLabel("<b>CLIENTE</b>"), 0, 0)
        self.input_cliente = QLineEdit("Venta mostrador")
        self.input_cliente.setReadOnly(True)
        self.input_cliente.setStyleSheet("background-color: #dcdde1; padding: 5px;")
        info_grid.addWidget(self.input_cliente, 0, 1)

        info_grid.addWidget(QLabel("<b>VENDEDOR</b>"), 1, 0)
        self.input_vendedor = QLineEdit(self.user_data['nombre'])
        self.input_vendedor.setReadOnly(True)
        self.input_vendedor.setStyleSheet("background-color: #dcdde1; padding: 5px;")
        info_grid.addWidget(self.input_vendedor, 1, 1)

        # Folio y Fecha
        info_grid.addWidget(QLabel("<b>FOLIO</b>"), 0, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        self.input_folio = QLineEdit("Generando...")
        self.input_folio.setReadOnly(True)
        self.input_folio.setStyleSheet("background-color: #dcdde1;")
        info_grid.addWidget(self.input_folio, 1, 2)

        info_grid.addWidget(QLabel("<b>FECHA</b>"), 0, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        self.input_fecha = QLineEdit(datetime.datetime.now().strftime('%d/%m/%Y'))
        self.input_fecha.setReadOnly(True)
        self.input_fecha.setStyleSheet("background-color: #dcdde1;")
        info_grid.addWidget(self.input_fecha, 1, 3)

        # Botón Venta Especial
        self.btn_especial = QPushButton("venta especial")
        self.btn_especial.setAutoDefault(False)
        self.btn_especial.setStyleSheet("background-color: red; color: white; font-weight: bold; padding: 5px;")
        self.btn_especial.clicked.connect(self.toggle_venta_especial)
        info_grid.addWidget(self.btn_especial, 2, 2, 1, 2) # Ocupa 2 columnas

        top_layout.addLayout(info_grid)
        top_layout.addStretch()

        # Tabla de Consulta de Stock (Arriba a la derecha)
        stock_layout = QVBoxLayout()
        lbl_stock = QLabel("<b>CONSULTA STOCK</b>")
        lbl_stock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stock_layout.addWidget(lbl_stock)
        
        self.tabla_stock = DataTable(["ALMACEN", "CANTIDAD"])
        self.tabla_stock.setFixedSize(300, 100)
        self.tabla_stock.setStyleSheet("background-color: #dcdde1;")
        stock_layout.addWidget(self.tabla_stock)
        
        top_layout.addLayout(stock_layout)
        main_layout.addLayout(top_layout)

        # ==========================================
        # MIDDLE SECTION: Buscador
        # ==========================================
        self.search_input = FormInput("Buscar producto por nombre o codigo f2")
        self.search_input.setStyleSheet("background-color: #dcdde1; padding: 8px; font-size: 14px;")
        # El evento returnPressed es perfecto para lectores de código de barras
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        main_layout.addWidget(self.search_input)

        # ==========================================
        # BOTTOM SECTION: Carrito y Totales
        # ==========================================
        main_layout.addWidget(QLabel("<b>Detalle de la Orden (Carrito):</b>"))
        
        columnas_carrito = ["", "codigo", "Producto", "Cant.", "desc", "Precio U.", "Subtotal"]
        self.tabla_carrito = DataTable(columnas_carrito)
        self.tabla_carrito.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.tabla_carrito.itemSelectionChanged.connect(self.actualizar_tabla_stock_seleccion)

        # Hacemos editable solo las columnas Cantidad (3) y Descuento (4)
        self.tabla_carrito.itemChanged.connect(self.recalcular_totales_por_edicion)
        main_layout.addWidget(self.tabla_carrito)

        footer_layout = QHBoxLayout()
        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        
        btn_cancelar = PrimaryButton("CANCELAR")
        btn_cancelar.setAutoDefault(False)
        btn_cancelar.setStyleSheet("background-color: #008f39; padding: 10px 20px;")
        btn_cancelar.clicked.connect(self.reject)
        
        self.btn_enviar = PrimaryButton("ENVIAR A CAJA F3")
        btn_cancelar.setAutoDefault(False)
        self.btn_enviar.setDefault(False)
        self.btn_enviar.setStyleSheet("background-color: #f39c12; padding: 10px 20px;")
        self.btn_enviar.clicked.connect(self.generate_order)

        self.btn_cotizar = PrimaryButton("GUARDAR COTIZACIÓN")
        self.btn_cotizar.setAutoDefault(False)
        self.btn_cotizar.setDefault(False)
        self.btn_cotizar.setStyleSheet("background-color: #f39c12; padding: 10px 20px;") # Color naranja
        self.btn_cotizar.clicked.connect(self.save_as_quotation)

        # --- NUEVO BOTÓN DE DESBLOQUEO ---
        self.btn_habilitar_edicion = PrimaryButton("✏️ Editar Orden")
        self.btn_habilitar_edicion.setAutoDefault(False)
        self.btn_habilitar_edicion.setStyleSheet("background-color: #f39c12; padding: 10px 20px;") # Naranja
        self.btn_habilitar_edicion.clicked.connect(self.desbloquear_edicion)
        self.btn_habilitar_edicion.hide() # Lo ocultamos inicialmente

        footer_layout.addWidget(self.lbl_total)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_cancelar)
        footer_layout.addWidget(self.btn_cotizar)
        footer_layout.addWidget(self.btn_habilitar_edicion)
        footer_layout.addWidget(self.btn_enviar)
        
        main_layout.addLayout(footer_layout)

    def setup_shortcuts(self):
        """Configura los atajos de teclado solicitados (guardados en self para que no se borren de memoria)"""
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        self.shortcut_f2.activated.connect(self.search_input.setFocus)
        
        self.shortcut_f3 = QShortcut(QKeySequence(Qt.Key.Key_F3), self)
        self.shortcut_f3.activated.connect(self.generate_order)

    def toggle_venta_especial(self):
        """Alterna el estado del cliente (Mostrador vs Especial)"""
        self.is_venta_especial = not self.is_venta_especial
        if self.is_venta_especial:
            self.input_cliente.setReadOnly(False)
            self.input_cliente.setStyleSheet("background-color: #ffffff; padding: 5px;")
            self.input_cliente.setText("")
            self.input_cliente.setPlaceholderText("Buscar cliente...")
            self.input_cliente.setFocus()
            self.btn_especial.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 5px;") # Verde
            self.btn_especial.setText("venta mostrador")
        else:
            self.input_cliente.setReadOnly(True)
            self.input_cliente.setStyleSheet("background-color: #dcdde1; padding: 5px;")
            self.input_cliente.setText("Venta mostrador")
            self.btn_especial.setStyleSheet("background-color: red; color: white; font-weight: bold; padding: 5px;")
            self.btn_especial.setText("venta especial")

        if self.is_venta_especial:
            # Aquí te muestro cómo reutilizaremos EXACTAMENTE EL MISMO MODAL pero para CLIENTES
            def query_clientes(busqueda):
                query = "SELECT rfc, nombre_completo, id_cliente FROM clientes WHERE estatus = TRUE AND (rfc ILIKE %s OR nombre_completo ILIKE %s)"
                term = f"%{busqueda}%"
                return self.db.fetch_all(query, (term, term))

            modal_cliente = GenericSearchModal(
                title="Buscar Cliente Especial",
                placeholder="Escribe el RFC o nombre del cliente",
                headers=["RFC", "NOMBRE DEL CLIENTE", "ID"],
                query_function=query_clientes,
                parent=self
            )

            if modal_cliente.exec():
                datos_cliente = modal_cliente.selected_data
                self.input_cliente.setText(datos_cliente[1]) # Ponemos el nombre en la barra

    def procesar_busqueda(self):
        """Se activa al dar 'Enter' en el buscador (escáner o manual)"""
        texto = self.search_input.text().strip()
        if not texto: return

        # Si el texto es puramente numérico (asumiendo que los códigos de barras lo son)
        if texto.isdigit():
            self.agregar_por_codigo_directo(texto)
        else:
            self.abrir_buscador_avanzado(texto)
            
        self.search_input.clear() # Limpiamos para el siguiente escaneo

    def agregar_por_codigo_directo(self, codigo):
        """Lógica para agregar producto directo vía lector de código de barras"""
        # 1. Buscamos el producto exacto
        query_prod = """
            SELECT id_producto, codigo, nombre, precio_venta 
            FROM productos 
            WHERE codigo = %s AND estatus = TRUE
        """
        producto = self.db.fetch_one(query_prod, (codigo,))
        
        if producto:
            id_prod, cod, nom, precio = producto
            
            # Lo metemos al carrito con cantidad 1 por defecto
            self.carrito.append({
                "id": id_prod, "codigo": cod, "nombre": nom, 
                "cant": 1.0, "desc": 0.0, 
                "precio": float(precio), "subtotal": float(precio)
            })
            self.update_cart_table()
            
            # 2. Buscamos su stock y llenamos la tabla de arriba a la derecha
            query_stock = """
                SELECT a.nombre, i.cantidad_existente 
                FROM inventario_almacen i
                JOIN almacenes a ON i.id_almacen = a.id_almacen
                WHERE i.id_producto = %s
            """
            stocks = self.db.fetch_all(query_stock, (id_prod,))
            self.tabla_stock.setRowCount(len(stocks))
            
            for i, (almacen, cantidad) in enumerate(stocks):
                self.tabla_stock.setItem(i, 0, QTableWidgetItem(almacen))
                self.tabla_stock.setItem(i, 1, QTableWidgetItem(str(cantidad)))
                
        else:
            QMessageBox.warning(self, "No encontrado", f"El código '{codigo}' no existe en la base de datos.")

    def abrir_buscador_avanzado(self, texto):
        """Abre el buscador reutilizable configurado para PRODUCTOS"""
        
        # 1. Definimos CÓMO va a buscar productos en la BD
        def query_productos(busqueda):
            query = """
                SELECT codigo, nombre, precio_venta, id_producto
                FROM productos 
                WHERE estatus = TRUE AND (codigo ILIKE %s OR nombre ILIKE %s)
                LIMIT 50
            """
            search_term = f"%{busqueda}%"
            return self.db.fetch_all(query, (search_term, search_term))

        # 2. Instanciamos el modal pasándole la función de arriba y los encabezados de tu imagen
        modal = GenericSearchModal(
            title="Buscar Producto",
            placeholder="Escribe el codigo o nombre del articulo para buscar",
            headers=["CODIGO", "NOMBRE ARTICULO", "Precio publico", "ID"],
            query_function=query_productos,
            parent=self
        )
        
        # 3. Si venía texto del buscador principal, se lo pegamos de una vez
        if texto:
            modal.search_input.setText(texto)
            
        # 4. Mostrar modal y esperar resultado
        if modal.exec():
            datos = modal.selected_data
            print("Producto seleccionado en el modal:", datos)
            
            codigo_seleccionado = datos[0]
            # Reutilizamos la función del escáner para meterlo al carrito
            self.agregar_por_codigo_directo(codigo_seleccionado)

    def recalcular_totales_por_edicion(self, item):
        """Detecta si el cajero editó la cantidad o el descuento y recalcula todo"""
        row = item.row()
        col = item.column()
        
        if col in [3, 4]: # Si editaron Cantidad o Descuento
            try:
                nuevo_valor = float(item.text())
                
                if col == 3:
                    self.carrito[row]['cant'] = nuevo_valor
                elif col == 4:
                    self.carrito[row]['desc'] = nuevo_valor
                
                # Recalculamos la matemática: (Precio * Cantidad) - Descuento
                precio = self.carrito[row]['precio']
                cant = self.carrito[row]['cant']
                desc = self.carrito[row]['desc']
                self.carrito[row]['subtotal'] = (precio * cant) - desc
                
                # Refrescamos la tabla para que se vea el nuevo subtotal
                self.update_cart_table()
                
            except ValueError:
                pass # Si el usuario escribió letras en vez de números, lo ignoramos

    def generate_order(self):
        """Guarda la orden nueva o actualiza una existente en la BD"""
        if not self.carrito:
            QMessageBox.warning(self, "Carrito vacío", "No hay productos en la orden.")
            return

        try:
            now = datetime.datetime.now()
            total = sum(p['subtotal'] for p in self.carrito)
            hora_limpia = now.strftime('%H:%M') 

            # ========================================================
            # ESCENARIO A: ESTAMOS ACTUALIZANDO UNA ORDEN EXISTENTE
            # ========================================================
            if self.folio_editar and self.modo_edicion_activo:
                
                # 1. Actualizamos el total y la hora en la cabecera
                query_upd = "UPDATE orden_venta SET total = %s, hora = %s WHERE id_venta = %s"
                self.db.execute_query(query_upd, (total, hora_limpia, self.id_venta_actual))

                # 2. El método Senior para carritos: Borrar todos los detalles viejos y reinsertar los nuevos
                # Esto evita tener que programar lógica compleja para saber qué producto quitó o agregó el usuario
                self.db.execute_query("DELETE FROM detalle_venta WHERE id_venta = %s", (self.id_venta_actual,))

                query_dv = """
                    INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                for p in self.carrito:
                    self.db.execute_query(query_dv, (self.id_venta_actual, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

                folio_final = self.folio_editar
                QMessageBox.information(self, "Éxito", f"Los cambios de la orden {folio_final} se guardaron correctamente.")

            # ========================================================
            # ESCENARIO B: ESTAMOS CREANDO UNA ORDEN NUEVA (Tu código original)
            # ========================================================
            else:
                folio_final = f"OV-{now.strftime('%Y%m%d%H%M%S')}"
                query_ov = """
                    INSERT INTO orden_venta (folio, id_vendedor, fecha, hora, id_cliente, total, estatus)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_venta
                """
                res = self.db.fetch_one(query_ov, (folio_final, self.user_data['id'], now.date(), hora_limpia, 1, total, 'Pendiente'))
                if not res: return
                id_venta_nuevo = res[0]

                query_dv = """
                    INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                for p in self.carrito:
                    self.db.execute_query(query_dv, (id_venta_nuevo, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

                QMessageBox.information(self, "Éxito", f"Orden {folio_final} generada y enviada a caja.")

            # Avisamos a las otras pantallas que actualicen sus tablas
            notificacion = {
                "tipo": "NUEVA_ORDEN",
                "folio": folio_final,
                "vendedor": self.user_data['nombre'],
                "total": total
            }
            self.ws_cliente.sendTextMessage(json.dumps(notificacion))
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la orden: {e}")
  
    def update_cart_table(self):
        self.tabla_carrito.blockSignals(True) 
        self.tabla_carrito.setRowCount(len(self.carrito))
        
        total = 0.0
        for i, prod in enumerate(self.carrito):
            # Creamos los items
            items = [
                QTableWidgetItem(">"),
                QTableWidgetItem(prod['codigo']),
                QTableWidgetItem(prod['nombre']),
                QTableWidgetItem(str(prod['cant'])),   # Col 3: Cantidad
                QTableWidgetItem(str(prod['desc'])),   # Col 4: Descuento
                QTableWidgetItem(f"{prod['precio']:.2f}"),
                QTableWidgetItem(f"{prod['subtotal']:.2f}")
            ]
            
            for col, item in enumerate(items):
                # Si NO es la columna 3 (Cant) ni la 4 (Desc), la hacemos SOLO LECTURA
                if col not in [3, 4]:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                # Opcional: Pintar de otro color las editables para que el cajero sepa
                else:
                    item.setBackground(Qt.GlobalColor.yellow) 
                    
                self.tabla_carrito.setItem(i, col, item)
            
            total += prod['subtotal']
            
        self.lbl_total.setText(f"Total: ${total:.2f}")
        self.tabla_carrito.blockSignals(False)
    
    def save_as_quotation(self):
        """Guarda una cotización nueva o actualiza una existente"""
        if not self.carrito:
            QMessageBox.warning(self, "Carrito vacío", "No hay productos.")
            return

        try:
            now = datetime.datetime.now()
            total = sum(p['subtotal'] for p in self.carrito)
            hora_limpia = now.strftime('%H:%M')

            # ESCENARIO: ACTUALIZAR COTIZACIÓN EXISTENTE
            if self.folio_editar and self.folio_editar.startswith("COT-") and self.modo_edicion_activo:
                # 1. Update cabecera
                self.db.execute_query("UPDATE cotizaciones SET total = %s, hora = %s WHERE id_cotizacion = %s", 
                                      (total, hora_limpia, self.id_venta_actual))
                
                # 2. Reemplazar detalles
                self.db.execute_query("DELETE FROM detalle_cotizacion WHERE id_cotizacion = %s", (self.id_venta_actual,))
                query_ins = """
                    INSERT INTO detalle_cotizacion (id_cotizacion, id_producto, cantidad, precio_unitario, descuento, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                for p in self.carrito:
                    self.db.execute_query(query_ins, (self.id_venta_actual, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))
                
                folio_final = self.folio_editar

            # ESCENARIO: NUEVA COTIZACIÓN
            else:
                folio_final = f"COT-{now.strftime('%Y%m%d%H%M%S')}"
                query_cot = """
                    INSERT INTO cotizaciones (folio, id_vendedor, fecha, hora, id_cliente, total)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_cotizacion
                """
                res = self.db.fetch_one(query_cot, (folio_final, self.user_data['id'], now.date(), hora_limpia, 1, total))
                id_cot = res[0]
                
                query_ins = """
                    INSERT INTO detalle_cotizacion (id_cotizacion, id_producto, cantidad, precio_unitario, descuento, subtotal)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                for p in self.carrito:
                    self.db.execute_query(query_ins, (id_cot, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

            # Notificar vía WebSocket
            self.ws_cliente.sendTextMessage(json.dumps({
                "tipo": "NUEVA_COTIZACION", "folio": folio_final, "vendedor": self.user_data['nombre'], "total": total
            }))
            
            QMessageBox.information(self, "Éxito", f"Cotización {folio_final} guardada.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar cotización: {e}")
    
    def actualizar_tabla_stock_seleccion(self):
        """Consulta el stock del producto seleccionado en el carrito"""
        current_row = self.tabla_carrito.currentRow()
        if current_row < 0: return # Si no hay nada seleccionado

        # Sacamos el ID o Código del producto del carrito (asumiendo que en la posición row está en tu lista self.carrito)
        id_prod = self.carrito[current_row]['id']

        query_stock = """
            SELECT a.nombre, i.cantidad_existente 
            FROM inventario_almacen i
            JOIN almacenes a ON i.id_almacen = a.id_almacen
            WHERE i.id_producto = %s
        """
        stocks = self.db.fetch_all(query_stock, (id_prod,))
        
        self.tabla_stock.setRowCount(len(stocks))
        for i, (almacen, cantidad) in enumerate(stocks):
            self.tabla_stock.setItem(i, 0, QTableWidgetItem(almacen))
            self.tabla_stock.setItem(i, 1, QTableWidgetItem(str(cantidad)))
    
    def keyPressEvent(self, event):
        """
        Sobrescribe el comportamiento del teclado del QDialog.
        Evita que la ventana se cierre o envíe la orden al presionar Enter/Intro.
        """
        # Verificamos si la tecla presionada es Enter (teclado normal) o Return (teclado numérico)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Ignoramos el evento a nivel de ventana. 
            # ¡Ojo! Esto NO afecta a tu buscador, porque el 'returnPressed' del QLineEdit 
            # se dispara antes de llegar aquí.
            event.ignore()
        else:
            # Si es cualquier otra tecla, dejamos que el sistema actúe normal
            super().keyPressEvent(event)
    
    def cargar_datos_para_edicion(self):
        """Carga datos de Orden de Venta o Cotización según el prefijo"""
        try:
            # Detectamos el tipo por el prefijo del folio
            es_cotizacion = self.folio_editar.startswith("COT-")
            
            if es_cotizacion:
                query_cabecera = """
                    SELECT v.id_cotizacion, c.nombre_completo, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), v.total
                    FROM cotizaciones v
                    JOIN clientes c ON v.id_cliente = c.id_cliente
                    WHERE v.folio = %s
                """
            else:
                query_cabecera = """
                    SELECT v.id_venta, c.nombre_completo, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), v.total, v.estatus
                    FROM orden_venta v
                    JOIN clientes c ON v.id_cliente = c.id_cliente
                    WHERE v.folio = %s
                """

            cabecera = self.db.fetch_one(query_cabecera, (self.folio_editar,))
            if not cabecera: return

            # Desempaquetamos (el estatus solo existe en órdenes de venta)
            id_db = cabecera[0]
            cliente, fecha, hora, total = cabecera[1], cabecera[2], cabecera[3], cabecera[4]
            estatus = cabecera[5] if not es_cotizacion else "Pendiente"
            
            self.id_venta_actual = id_db # Guardamos el ID para el UPDATE
            self.input_folio.setText(self.folio_editar)
            self.input_cliente.setText(cliente)
            self.input_fecha.setText(str(fecha))

            # Consultamos los detalles (productos) de la tabla correspondiente
            tabla_detalle = "detalle_cotizacion" if es_cotizacion else "detalle_venta"
            campo_id = "id_cotizacion" if es_cotizacion else "id_venta"
            
            query_detalles = f"""
                SELECT p.id_producto, p.codigo, p.nombre, d.cantidad, d.descuento, d.precio_unitario, d.subtotal
                FROM {tabla_detalle} d
                JOIN productos p ON d.id_producto = p.id_producto
                WHERE d.{campo_id} = %s
            """
            detalles = self.db.fetch_all(query_detalles, (id_db,))
            
            self.carrito = [] # Limpiamos antes de cargar
            for d in detalles:
                self.carrito.append({
                    "id": d[0], "codigo": d[1], "nombre": d[2],
                    "cant": float(d[3]), "desc": float(d[4]),
                    "precio": float(d[5]), "subtotal": float(d[6])
                })
            
            self.update_cart_table()
            self.bloquear_todo_modo_lectura()

            # Solo mostramos el botón de editar si no está cobrada (si es OV) o si es COT
            if estatus != 'Cobrada':
                self.btn_habilitar_edicion.show()

        except Exception as e:
            print(f"Error al cargar edición: {e}")
    
    def bloquear_todo_modo_lectura(self):
        """Bloquea la interfaz para que funcione solo como visor"""
        self.search_input.setEnabled(False)
        self.search_input.setPlaceholderText("Modo Vista Previa - Da clic en 'Editar Orden' para hacer cambios")
        self.btn_enviar.setEnabled(False)
        self.btn_cotizar.setEnabled(False)
        self.btn_especial.setEnabled(False)
        # Bloquear tabla del carrito
        from PyQt6.QtWidgets import QAbstractItemView
        self.tabla_carrito.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def desbloquear_edicion(self):
        """Quita el candado y permite hacer cambios"""
        self.modo_edicion_activo = True
        self.setWindowTitle(f"EDITANDO: {self.folio_editar} - El Tornillo Feliz")
        
        self.search_input.setEnabled(True)
        self.search_input.setPlaceholderText("Buscar producto por nombre o codigo f2")
        
        self.btn_enviar.setEnabled(True)
        self.btn_enviar.setText("GUARDAR CAMBIOS F3")
        self.btn_enviar.setStyleSheet("background-color: #27ae60; padding: 10px 20px;") # Verde para indicar guardado
        
        self.btn_cotizar.setEnabled(True)
        self.btn_especial.setEnabled(True)
        self.btn_habilitar_edicion.hide() # Escondemos el botón de desbloqueo porque ya está desbloqueado
        
        from PyQt6.QtWidgets import QAbstractItemView
        self.tabla_carrito.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        
        QMessageBox.information(self, "Edición Habilitada", "Ya puedes agregar o quitar productos, o modificar cantidades.")