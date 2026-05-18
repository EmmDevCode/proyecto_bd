# frontend/views/modulo_compras.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QCheckBox, QDialog, QComboBox, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom
from frontend.components.elementos_ui import BotonNuevo, DataTable, BotonConfirmar, BotonBuscar
from frontend.components.modulo_consulta import ModuloConsulta
from frontend.components.buscador import GenericSearchModal

class VentanaNuevaCompra(QDialog):
    """Formulario dual para registrar o EDITAR una factura de proveedor"""
    def __init__(self, folio_editar=None, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.folio_editar = folio_editar # Si viene con folio, es modo Edición
        self.id_compra_editar = None
        self.productos_compra = [] 
        
        self.id_proveedor_seleccionado = None
        self.producto_temporal = None 
        
        self.init_ui()
        self.cargar_almacenes()
        
        # --- NUEVO: Permitir borrar items con doble clic ---
        self.tabla_items.doubleClicked.connect(self.remover_item)
        
        # Si estamos en modo edición, cargamos los datos
        if self.folio_editar:
            self.cargar_datos_edicion()

    def init_ui(self):
        titulo = "Editar Compra de Inventario" if self.folio_editar else "Registrar Compra de Inventario"
        self.setWindowTitle(titulo)
        self.setMinimumWidth(950)
        self.setMinimumHeight(600)
        self.showMaximized()
        self.setStyleSheet("background-color: white;")

        layout_principal = QHBoxLayout(self)

        # ==========================================
        # PANEL IZQUIERDO: Datos de Factura y Buscadores
        # ==========================================
        panel_izq = QVBoxLayout()
        form_layout = QFormLayout()
        
        ly_prov = QHBoxLayout()
        self.input_proveedor = QLineEdit()
        self.input_proveedor.setReadOnly(True)
        self.input_proveedor.setPlaceholderText("Seleccione un proveedor...")
        
        btn_buscar_prov = BotonBuscar("Buscar")
        btn_buscar_prov.clicked.connect(self.abrir_buscador_proveedor)
        ly_prov.addWidget(self.input_proveedor)
        ly_prov.addWidget(btn_buscar_prov)
        
        self.combo_almacen = QComboBox()
        
        self.input_factura = QLineEdit()
        self.input_factura.setPlaceholderText("Ej. ABC-12345")
        
        form_layout.addRow("Proveedor:", ly_prov)
        form_layout.addRow("Almacén Destino:", self.combo_almacen)
        form_layout.addRow("No. Factura:", self.input_factura)
        
        panel_izq.addLayout(form_layout)
        panel_izq.addSpacing(20)

        panel_izq.addWidget(QLabel("<b>Añadir Productos:</b>"))
        
        ly_prod = QHBoxLayout()
        self.input_producto = QLineEdit()
        self.input_producto.setReadOnly(True)
        self.input_producto.setPlaceholderText("Ningún producto seleccionado...")
        
        btn_buscar_prod = BotonBuscar("Buscar Producto")
        btn_buscar_prod.clicked.connect(self.abrir_buscador_producto)
        ly_prod.addWidget(self.input_producto)
        ly_prod.addWidget(btn_buscar_prod)
        panel_izq.addLayout(ly_prod)
        
        ly_add = QHBoxLayout()
        self.input_cantidad = QSpinBox()
        self.input_cantidad.setRange(1, 99999)
        btn_add = QPushButton("+ Agregar a la lista")
        btn_add.clicked.connect(self.agregar_a_lista)
        btn_add.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
        
        ly_add.addWidget(QLabel("Cantidad:"))
        ly_add.addWidget(self.input_cantidad)
        ly_add.addWidget(btn_add)
        panel_izq.addLayout(ly_add)
        
        panel_izq.addWidget(QLabel("<i>* Doble clic en un elemento de la tabla para quitarlo</i>"))
        panel_izq.addStretch()

        # ==========================================
        # PANEL DERECHO: Detalle, Impuestos y Totales
        # ==========================================
        panel_der = QVBoxLayout()
        self.tabla_items = DataTable(["ID", "Código", "Producto", "Cant", "Costo Unit.", "Subtotal"])
        panel_der.addWidget(self.tabla_items)

        self.check_iva = QCheckBox("Aplicar 16% de IVA a la factura")
        self.check_iva.setChecked(True)
        self.check_iva.stateChanged.connect(self.actualizar_totales)
        panel_der.addWidget(self.check_iva, alignment=Qt.AlignmentFlag.AlignRight)

        self.lbl_subtotal = QLabel("Subtotal: $0.00")
        self.lbl_iva = QLabel("IVA (16%): $0.00")
        self.lbl_total = QLabel("TOTAL COMPRA: $0.00")
        
        estilo_totales = "font-size: 16px; color: #7f8c8d;"
        self.lbl_subtotal.setStyleSheet(estilo_totales)
        self.lbl_iva.setStyleSheet(estilo_totales)
        self.lbl_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        
        panel_der.addWidget(self.lbl_subtotal, alignment=Qt.AlignmentFlag.AlignRight)
        panel_der.addWidget(self.lbl_iva, alignment=Qt.AlignmentFlag.AlignRight)
        panel_der.addWidget(self.lbl_total, alignment=Qt.AlignmentFlag.AlignRight)

        texto_btn = "GUARDAR CAMBIOS" if self.folio_editar else "CONFIRMAR ABASTECIMIENTO"
        btn_confirmar = BotonConfirmar(texto_btn)
        btn_confirmar.clicked.connect(self.procesar_compra)
        panel_der.addWidget(btn_confirmar)

        layout_principal.addLayout(panel_izq, 1)
        layout_principal.addLayout(panel_der, 3)

    # ==========================================
    # LÓGICA DE EDICIÓN
    # ==========================================
    def cargar_datos_edicion(self):
        """Carga los datos de la compra existente en la BD"""
        # 1. Datos Generales
        query_cabecera = """
            SELECT c.id_compra, c.id_proveedor, p.nombre, p.rfc, c.id_almacen_destino, c.numero_factura, c.impuestos_totales
            FROM compras c
            JOIN proveedores p ON c.id_proveedor = p.id_proveedor
            WHERE c.folio_interno = %s
        """
        res = self.db.fetch_one(query_cabecera, (self.folio_editar,))
        if not res: return
        
        self.id_compra_editar = res[0]
        self.id_proveedor_seleccionado = res[1]
        self.input_proveedor.setText(f"{res[2]} ({res[3]})")
        
        # Seleccionar el almacén en el combo
        index_alm = self.combo_almacen.findData(res[4])
        if index_alm >= 0: self.combo_almacen.setCurrentIndex(index_alm)
        
        self.input_factura.setText(res[5])
        
        # Detectar si tenía IVA (Si impuestos > 0, marcamos el checkbox)
        self.check_iva.setChecked(float(res[6]) > 0)

        # 2. Detalles de los productos
        query_detalles = """
            SELECT d.id_producto, p.codigo, p.nombre, d.cantidad, d.precio_compra, d.subtotal
            FROM detalle_compra d
            JOIN productos p ON d.id_producto = p.id_producto
            WHERE d.id_compra = %s
        """
        detalles = self.db.fetch_all(query_detalles, (self.id_compra_editar,))
        
        for d in (detalles or []):
            prod = {
                "id": d[0], "cod": d[1], "nom": d[2], 
                "cant": float(d[3]), "costo": float(d[4]), "sub": float(d[5])
            }
            self.productos_compra.append(prod)
            
        self.refrescar_tabla()

    # ==========================================
    # LÓGICA DE CATÁLOGOS Y BUSCADOR
    # ==========================================
    def cargar_almacenes(self):
        alms = self.db.fetch_all("SELECT id_almacen, nombre FROM almacenes WHERE estatus=TRUE")
        for a in (alms or []): self.combo_almacen.addItem(a[1], a[0])

    def query_proveedores(self, texto):
        filtro = f"%{texto}%"
        return self.db.fetch_all("SELECT id_proveedor, rfc, nombre FROM proveedores WHERE estatus=TRUE AND (nombre ILIKE %s OR rfc ILIKE %s)", (filtro, filtro))

    def query_productos(self, texto):
        filtro = f"%{texto}%"
        return self.db.fetch_all("SELECT id_producto, codigo, nombre, precio_compra FROM productos WHERE estatus=TRUE AND (codigo ILIKE %s OR nombre ILIKE %s)", (filtro, filtro))

    def abrir_buscador_proveedor(self):
        modal = GenericSearchModal("Buscar Proveedor", "Escribe nombre o RFC...", ["ID", "RFC", "Nombre"], self.query_proveedores, self)
        if modal.exec():
            data = modal.selected_data
            self.id_proveedor_seleccionado = data[0]
            self.input_proveedor.setText(f"{data[2]} ({data[1]})")

    def abrir_buscador_producto(self):
        modal = GenericSearchModal("Buscar Producto", "Escribe código o nombre...", ["ID", "Código", "Nombre", "Costo"], self.query_productos, self)
        if modal.exec():
            data = modal.selected_data
            self.producto_temporal = {"id": data[0], "cod": data[1], "nom": data[2], "costo": float(data[3])}
            self.input_producto.setText(f"{data[1]} - {data[2]} (Costo: ${self.producto_temporal['costo']:.2f})")

    # ==========================================
    # LÓGICA DE NEGOCIO (TABLA Y BD)
    # ==========================================
    def agregar_a_lista(self):
        if not self.producto_temporal:
            AlertaCustom.show_warning(self, "Aviso", "Primero busca y selecciona un producto.")
            return
            
        cant = self.input_cantidad.value()
        subtotal_linea = cant * self.producto_temporal['costo']
        
        # Revisamos si el producto ya está en la lista para sumar la cantidad
        encontrado = False
        for p in self.productos_compra:
            if p['id'] == self.producto_temporal['id']:
                p['cant'] += cant
                p['sub'] = p['cant'] * p['costo']
                encontrado = True
                break
                
        if not encontrado:
            self.productos_compra.append({
                "id": self.producto_temporal['id'], "cod": self.producto_temporal['cod'],
                "nom": self.producto_temporal['nom'], "cant": cant, 
                "costo": self.producto_temporal['costo'], "sub": subtotal_linea
            })
        
        self.refrescar_tabla()
        
        self.producto_temporal = None
        self.input_producto.clear()
        self.input_cantidad.setValue(1)

    def remover_item(self, index):
        """Permite borrar una fila de la tabla con doble clic"""
        fila = index.row()
        del self.productos_compra[fila]
        self.refrescar_tabla()

    def refrescar_tabla(self):
        self.tabla_items.setRowCount(0)
        for p in self.productos_compra:
            row = self.tabla_items.rowCount()
            self.tabla_items.insertRow(row)
            self.tabla_items.setItem(row, 0, QTableWidgetItem(str(p['id'])))
            self.tabla_items.setItem(row, 1, QTableWidgetItem(p['cod']))
            self.tabla_items.setItem(row, 2, QTableWidgetItem(p['nom']))
            self.tabla_items.setItem(row, 3, QTableWidgetItem(str(p['cant'])))
            self.tabla_items.setItem(row, 4, QTableWidgetItem(f"${p['costo']:,.2f}"))
            self.tabla_items.setItem(row, 5, QTableWidgetItem(f"${p['sub']:,.2f}"))
        self.actualizar_totales()

    def actualizar_totales(self):
        subtotal = sum(p['sub'] for p in self.productos_compra)
        impuestos = subtotal * 0.16 if self.check_iva.isChecked() else 0.0
        total = subtotal + impuestos

        self.compra_subtotal = subtotal
        self.compra_impuestos = impuestos
        self.compra_total = total

        self.lbl_subtotal.setText(f"Subtotal: ${subtotal:,.2f}")
        self.lbl_iva.setText(f"IVA (16%): ${impuestos:,.2f}")
        self.lbl_total.setText(f"TOTAL COMPRA: ${total:,.2f}")

    def procesar_compra(self):
        if not self.productos_compra or not self.input_factura.text() or not self.id_proveedor_seleccionado:
            AlertaCustom.show_warning(self, "Incompleto", "Verifica proveedor, productos y No. de factura.")
            return

        id_alm = self.combo_almacen.currentData()

        # ==========================================
        # EL ALGORITMO DE SEGURIDAD (CÁLCULO DE DELTAS)
        # ==========================================
        if self.id_compra_editar:
            # 1. Obtener lo que había antes
            old_items = self.db.fetch_all("SELECT id_producto, cantidad FROM detalle_compra WHERE id_compra = %s", (self.id_compra_editar,))
            old_dict = {row[0]: float(row[1]) for row in (old_items or [])}
            
            # 2. Obtener lo que hay ahora en la tabla
            new_dict = {p['id']: p['cant'] for p in self.productos_compra}
            
            # 3. Validar que no dejemos stock negativo
            ids_totales = set(old_dict.keys()).union(new_dict.keys())
            for prod_id in ids_totales:
                delta = new_dict.get(prod_id, 0.0) - old_dict.get(prod_id, 0.0)
                
                # Si el delta es negativo, significa que estamos quitando stock de la compra
                if delta < 0:
                    stock_actual = self.db.fetch_one("SELECT cantidad_existente, p.nombre FROM inventario_almacen ia JOIN productos p ON ia.id_producto = p.id_producto WHERE ia.id_producto = %s AND ia.id_almacen = %s", (prod_id, id_alm))
                    if stock_actual:
                        existencia = float(stock_actual[0])
                        nombre = stock_actual[1]
                        if existencia + delta < 0:
                            AlertaCustom.show_error(self, "Protección de Inventario", f"No puedes reducir la factura de:\n'{nombre}'\n\nYa vendiste estos productos y tu stock quedaría en negativo.")
                            return # ¡ABORTAMOS EL GUARDADO!

        # Si pasamos la validación (o es compra nueva), procedemos a guardar
        if AlertaCustom.ask_confirm(self, "Confirmar", "¿Guardar los cambios en el sistema?"):
            try:
                if self.id_compra_editar:
                    # MODO EDICIÓN
                    # A. Actualizar cabecera
                    self.db.execute_query("""
                        UPDATE compras SET id_proveedor=%s, id_almacen_destino=%s, numero_factura=%s, impuestos_totales=%s, total_compra=%s 
                        WHERE id_compra=%s
                    """, (self.id_proveedor_seleccionado, id_alm, self.input_factura.text(), self.compra_impuestos, self.compra_total, self.id_compra_editar))
                    
                    # B. Aplicar diferencias al inventario
                    for prod_id in ids_totales:
                        delta = new_dict.get(prod_id, 0.0) - old_dict.get(prod_id, 0.0)
                        if delta != 0:
                            self.db.execute_query("UPDATE inventario_almacen SET cantidad_existente = cantidad_existente + %s WHERE id_producto = %s AND id_almacen = %s", (delta, prod_id, id_alm))
                    
                    # C. Reemplazar detalles
                    self.db.execute_query("DELETE FROM detalle_compra WHERE id_compra=%s", (self.id_compra_editar,))
                    for p in self.productos_compra:
                        self.db.execute_query("INSERT INTO detalle_compra (id_compra, id_producto, cantidad, precio_compra, subtotal) VALUES (%s, %s, %s, %s, %s)", 
                                            (self.id_compra_editar, p['id'], p['cant'], p['costo'], p['sub']))
                    
                    AlertaCustom.show_success(self, "Éxito", "Compra actualizada correctamente.")
                
                else:
                    # MODO CREACIÓN (El código que ya tenías)
                    folio_int = f"CMP-{self.input_factura.text()}"
                    res = self.db.fetch_one("""
                        INSERT INTO compras (folio_interno, id_proveedor, id_almacen_destino, numero_factura, fecha, tipo_cambio, impuestos_totales, total_compra)
                        VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s, %s) RETURNING id_compra
                    """, (folio_int, self.id_proveedor_seleccionado, id_alm, self.input_factura.text(), 1.0, self.compra_impuestos, self.compra_total))
                    
                    id_compra_db = res[0]

                    for p in self.productos_compra:
                        self.db.execute_query("INSERT INTO detalle_compra (id_compra, id_producto, cantidad, precio_compra, subtotal) VALUES (%s, %s, %s, %s, %s)", 
                                            (id_compra_db, p['id'], p['cant'], p['costo'], p['sub']))

                        query_stock = """
                            INSERT INTO inventario_almacen (id_almacen, id_producto, cantidad_existente) VALUES (%s, %s, %s)
                            ON CONFLICT (id_almacen, id_producto) DO UPDATE SET cantidad_existente = inventario_almacen.cantidad_existente + EXCLUDED.cantidad_existente;
                        """
                        self.db.execute_query(query_stock, (id_alm, p['id'], p['cant']))
                    
                    AlertaCustom.show_success(self, "Éxito", f"Compra registrada exitosamente.\nFolio: {folio_int}")
                
                self.accept()
            except Exception as e:
                AlertaCustom.show_error(self, "Error BD", f"No se pudo procesar: {e}")

class ModuloCompras(QWidget):
    """Vista principal para ver el historial de abastecimiento"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        header = QHBoxLayout()
        header.addStretch()
        
        self.btn_nueva = BotonNuevo("Registrar Factura Compra")
        self.btn_nueva.clicked.connect(self.abrir_formulario_nuevo)
        header.addWidget(self.btn_nueva)
        layout.addLayout(header)

        query_compras = """
            SELECT c.folio_interno, c.numero_factura, p.nombre, a.nombre, c.fecha, c.total_compra
            FROM compras c
            JOIN proveedores p ON c.id_proveedor = p.id_proveedor
            JOIN almacenes a ON c.id_almacen_destino = a.id_almacen
            WHERE c.fecha = %s
            ORDER BY c.fecha DESC
        """
        
        # --- NUEVO: Inyectamos el menú de opciones para que aparezca al dar clic derecho ---
        menu_opciones = {
            "Editar Factura": self.abrir_formulario_edicion
        }
        
        self.historial_compras = ModuloConsulta(
            titulo="HISTORIAL DE ABASTECIMIENTO",
            columnas=["Folio", "Factura", "Proveedor", "Almacén", "Fecha", "Total"],
            query_base=query_compras,
            menu_opciones=menu_opciones
        )
        layout.addWidget(self.historial_compras)

    def abrir_formulario_nuevo(self):
        if VentanaNuevaCompra(parent=self).exec():
            self.historial_compras.cargar_datos_del_dia()
            
    def abrir_formulario_edicion(self, folio):
        if VentanaNuevaCompra(folio_editar=folio, parent=self).exec():
            self.historial_compras.cargar_datos_del_dia()