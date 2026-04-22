# frontend/views/modulo_compras.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QCheckBox, QDialog, QComboBox, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom
from frontend.components.elementos_ui import PrimaryButton, DataTable
from frontend.components.buscador import GenericSearchModal
from frontend.components.elementos_ui import BotonNuevo, DataTable, BotonConfirmar, BotonBuscar

class VentanaNuevaCompra(QDialog):
    """Formulario para registrar una nueva factura de proveedor"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.productos_compra = [] 
        
        # Variables para almacenar selecciones del modal
        self.id_proveedor_seleccionado = None
        self.producto_temporal = None 
        
        self.init_ui()
        self.cargar_almacenes()

    def init_ui(self):
        self.setWindowTitle("Registrar Compra de Inventario")
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
        
        # 1. Buscador de Proveedor (Usando tu Modal)
        ly_prov = QHBoxLayout()
        self.input_proveedor = QLineEdit()
        self.input_proveedor.setReadOnly(True)
        self.input_proveedor.setPlaceholderText("Seleccione un proveedor...")
        
        btn_buscar_prov = BotonBuscar("Buscar")
        btn_buscar_prov.clicked.connect(self.abrir_buscador_proveedor)
        ly_prov.addWidget(self.input_proveedor)
        ly_prov.addWidget(btn_buscar_prov)
        
        # 2. Selector de Almacén (ComboBox normal)
        self.combo_almacen = QComboBox()
        
        # 3. Número de Factura
        self.input_factura = QLineEdit()
        self.input_factura.setPlaceholderText("Ej. ABC-12345")
        
        form_layout.addRow("Proveedor:", ly_prov)
        form_layout.addRow("Almacén Destino:", self.combo_almacen)
        form_layout.addRow("No. Factura:", self.input_factura)
        
        panel_izq.addLayout(form_layout)
        panel_izq.addSpacing(20)

        # 4. Buscador de Productos (Usando tu Modal)
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
        
        # Cantidad y Botón de Agregar
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
        
        panel_izq.addStretch()

        # ==========================================
        # PANEL DERECHO: Detalle, Impuestos y Totales
        # ==========================================
        panel_der = QVBoxLayout()
        self.tabla_items = DataTable(["ID", "Código", "Producto", "Cant", "Costo Unit.", "Subtotal"])
        panel_der.addWidget(self.tabla_items)

        # Controles de Impuestos
        self.check_iva = QCheckBox("Aplicar 16% de IVA a la factura")
        self.check_iva.setChecked(True)
        self.check_iva.stateChanged.connect(self.actualizar_totales)
        panel_der.addWidget(self.check_iva, alignment=Qt.AlignmentFlag.AlignRight)

        # Etiquetas de Totales
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

        btn_confirmar = BotonConfirmar("CONFIRMAR ABASTECIMIENTO")
        btn_confirmar.clicked.connect(self.procesar_compra)
        panel_der.addWidget(btn_confirmar)

        layout_principal.addLayout(panel_izq, 1)
        layout_principal.addLayout(panel_der, 3)

    # ==========================================
    # LÓGICA DE CATÁLOGOS Y BUSCADOR (MODAL)
    # ==========================================
    def cargar_almacenes(self):
        alms = self.db.fetch_all("SELECT id_almacen, nombre FROM almacenes WHERE estatus=TRUE")
        for a in (alms or []): self.combo_almacen.addItem(a[1], a[0])

    # --- Consultas para tu Modal ---
    def query_proveedores(self, texto):
        filtro = f"%{texto}%"
        return self.db.fetch_all("SELECT id_proveedor, rfc, nombre FROM proveedores WHERE estatus=TRUE AND (nombre ILIKE %s OR rfc ILIKE %s)", (filtro, filtro))

    def query_productos(self, texto):
        filtro = f"%{texto}%"
        return self.db.fetch_all("SELECT id_producto, codigo, nombre, precio_compra FROM productos WHERE estatus=TRUE AND (codigo ILIKE %s OR nombre ILIKE %s)", (filtro, filtro))

    # --- Apertura de Modales ---
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
            # data[3] es el precio_compra, lo pasamos a float
            self.producto_temporal = {
                "id": data[0], "cod": data[1], "nom": data[2], "costo": float(data[3])
            }
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
        
        row = self.tabla_items.rowCount()
        self.tabla_items.insertRow(row)
        self.tabla_items.setItem(row, 0, QTableWidgetItem(str(self.producto_temporal['id'])))
        self.tabla_items.setItem(row, 1, QTableWidgetItem(self.producto_temporal['cod']))
        self.tabla_items.setItem(row, 2, QTableWidgetItem(self.producto_temporal['nom']))
        self.tabla_items.setItem(row, 3, QTableWidgetItem(str(cant)))
        self.tabla_items.setItem(row, 4, QTableWidgetItem(f"${self.producto_temporal['costo']:,.2f}"))
        self.tabla_items.setItem(row, 5, QTableWidgetItem(f"${subtotal_linea:,.2f}"))
        
        self.productos_compra.append({
            "id": self.producto_temporal['id'], "cant": cant, 
            "costo": self.producto_temporal['costo'], "sub": subtotal_linea
        })
        
        self.actualizar_totales()
        
        # Limpiamos para el siguiente producto
        self.producto_temporal = None
        self.input_producto.clear()
        self.input_cantidad.setValue(1)

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
        folio_int = f"CMP-{self.input_factura.text()}"

        if AlertaCustom.ask_confirm(self, "Confirmar", "¿Registrar esta compra y aumentar el inventario?"):
            try:
                query_compra = """
                    INSERT INTO compras (folio_interno, id_proveedor, id_almacen_destino, numero_factura, 
                                         fecha, tipo_cambio, impuestos_totales, total_compra)
                    VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s, %s) RETURNING id_compra
                """
                res = self.db.fetch_one(query_compra, (folio_int, self.id_proveedor_seleccionado, id_alm, 
                                                       self.input_factura.text(), 1.0, self.compra_impuestos, self.compra_total))
                id_compra_db = res[0]

                for p in self.productos_compra:
                    self.db.execute_query("""
                        INSERT INTO detalle_compra (id_compra, id_producto, cantidad, precio_compra, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (id_compra_db, p['id'], p['cant'], p['costo'], p['sub']))

                    query_stock = """
                        INSERT INTO inventario_almacen (id_almacen, id_producto, cantidad_existente)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id_almacen, id_producto) 
                        DO UPDATE SET cantidad_existente = inventario_almacen.cantidad_existente + EXCLUDED.cantidad_existente;
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
        lbl = QLabel("HISTORIAL DE ABASTECIMIENTO (COMPRAS)")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(lbl)
        
        btn_nueva = BotonNuevo("Registrar Factura Compra")
        btn_nueva.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        btn_nueva.clicked.connect(self.abrir_formulario)
        header.addWidget(btn_nueva)
        layout.addLayout(header)

        self.tabla = DataTable(["Folio", "Factura", "Proveedor", "Almacén", "Fecha", "Total"])
        layout.addWidget(self.tabla)
        self.cargar_datos()

    def cargar_datos(self):
        query = """
            SELECT c.folio_interno, c.numero_factura, p.nombre, a.nombre, c.fecha, c.total_compra
            FROM compras c
            JOIN proveedores p ON c.id_proveedor = p.id_proveedor
            JOIN almacenes a ON c.id_almacen_destino = a.id_almacen
            ORDER BY c.fecha DESC
        """
        res = self.db.fetch_all(query)
        self.tabla.setRowCount(0)
        for i, fila in enumerate(res or []):
            self.tabla.insertRow(i)
            for j, val in enumerate(fila):
                item = QTableWidgetItem(f"${val:,.2f}" if j == 5 else str(val))
                self.tabla.setItem(i, j, item)

    def abrir_formulario(self):
        if VentanaNuevaCompra(self).exec():
            self.cargar_datos()