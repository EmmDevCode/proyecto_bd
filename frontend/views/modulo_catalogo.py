# frontend/views/modulo_catalogo.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QFormLayout, QComboBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom
from frontend.components.elementos_ui import BotonGuardar, BotonEditar, BotonBaja, BotonNuevo, InputBuscador
import qtawesome as qta

class FormularioProducto(QDialog):
    """Modal para Alta y Edición de Productos"""
    def __init__(self, db, producto_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.producto_id = producto_id
        self.init_ui()
        if self.producto_id:
            self.cargar_datos()

    def init_ui(self):
        self.setWindowTitle("Nuevo Producto" if not self.producto_id else "Editar Producto")
        self.setFixedWidth(480) # Lo hice un poquito más ancho para que quepa el botón
        self.setStyleSheet("background-color: white; font-size: 14px;")
        
        layout = QFormLayout(self)
        layout.setSpacing(15)

        # --- CAMPO DE CÓDIGO CON BOTÓN GENERADOR ---
        ly_codigo = QHBoxLayout()
        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Escanee o escriba el código...")
        
        self.btn_generar_lt = QPushButton(" Generar LT")
        self.btn_generar_lt.setIcon(qta.icon('fa5s.magic', color='white'))
        self.btn_generar_lt.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 5px 10px; border-radius: 3px;")
        self.btn_generar_lt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generar_lt.clicked.connect(self.generar_codigo_interno)
        
        # Si estamos editando, ocultamos el botón para no cambiar el código por error
        if self.producto_id:
            self.btn_generar_lt.hide()

        ly_codigo.addWidget(self.input_codigo)
        ly_codigo.addWidget(self.btn_generar_lt)

        # Resto de campos
        self.input_nombre = QLineEdit()
        self.input_unidad = QLineEdit()
        self.input_unidad.setPlaceholderText("Ej. Pieza, Metro, Caja")

        self.spin_compra = QDoubleSpinBox(); self.spin_compra.setMaximum(999999)
        self.spin_venta = QDoubleSpinBox(); self.spin_venta.setMaximum(999999)
        self.spin_mayoreo = QDoubleSpinBox(); self.spin_mayoreo.setMaximum(999999)
        self.spin_impuesto = QDoubleSpinBox(); self.spin_impuesto.setMaximum(100)
        
        self.combo_proveedor = QComboBox()
        self.cargar_proveedores()

        # Añadir al formulario
        layout.addRow("Código de Articulo:", ly_codigo)
        layout.addRow("Nombre / Descripción:", self.input_nombre)
        layout.addRow("Precio Compra ($):", self.spin_compra)
        layout.addRow("Precio Venta ($):", self.spin_venta)
        layout.addRow("Precio Mayoreo ($):", self.spin_mayoreo)
        layout.addRow("Impuesto (%):", self.spin_impuesto)
        layout.addRow("Unidad de Medida:", self.input_unidad)
        layout.addRow("Proveedor (Opcional):", self.combo_proveedor)

        # Botones
        btn_layout = QHBoxLayout()
        btn_guardar = BotonGuardar("Guardar")
        btn_guardar.clicked.connect(self.guardar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #95a5a6; color: white; padding: 10px; border-radius: 4px;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addRow(btn_layout)

    def generar_codigo_interno(self):
        """Busca los códigos LT en la BD y genera el siguiente sin guion"""
        # Traemos todos los códigos que empiecen con LT (tengan guion o no)
        query = "SELECT codigo FROM productos WHERE codigo LIKE 'LT%'"
        try:
            resultados = self.db.fetch_all(query)
            max_num = 0
            
            for fila in (resultados or []):
                codigo_actual = fila[0]
                # Limpiamos el texto: quitamos "LT-" y "LT" para dejar solo los números
                num_str = codigo_actual.replace("LT-", "").replace("LT", "")
                
                # Verificamos que lo que quedó sea un número válido
                if num_str.isdigit():
                    numero = int(num_str)
                    if numero > max_num:
                        max_num = numero
                        
            nuevo_numero = max_num + 1
            
            # Formateamos SIN guion y con 4 dígitos (ej. LT0001, LT0002)
            nuevo_codigo = f"LT{nuevo_numero:04d}"
            self.input_codigo.setText(nuevo_codigo)
            
        except Exception as e:
            AlertaCustom.show_error(self, "Error", f"No se pudo generar el código: {e}")

    def cargar_proveedores(self):
        try:
            proveedores = self.db.fetch_all("SELECT id_proveedor, nombre FROM proveedores WHERE estatus = TRUE")
            # Volvemos a pedir que seleccionen uno obligatoriamente
            self.combo_proveedor.addItem("-- Seleccione Proveedor --", None)
            for prov in (proveedores or []):
                self.combo_proveedor.addItem(prov[1], prov[0])
        except Exception:
            pass

    def cargar_datos(self):
        query = "SELECT codigo, nombre, precio_compra, precio_venta, precio_mayoreo, impuesto, unidad_medida, id_proveedor FROM productos WHERE id_producto = %s"
        res = self.db.fetch_one(query, (self.producto_id,))
        if res:
            self.input_codigo.setText(res[0])
            self.input_nombre.setText(res[1])
            self.spin_compra.setValue(float(res[2]))
            self.spin_venta.setValue(float(res[3]))
            self.spin_mayoreo.setValue(float(res[4]))
            self.spin_impuesto.setValue(float(res[5]))
            self.input_unidad.setText(res[6])
            
            # Buscar el proveedor en el combo
            index = self.combo_proveedor.findData(res[7])
            if index >= 0: self.combo_proveedor.setCurrentIndex(index)

    def guardar(self):
        cod = self.input_codigo.text().strip()
        nom = self.input_nombre.text().strip()
        prov_id = self.combo_proveedor.currentData() 

        # Volvemos a hacer obligatorio el proveedor
        if not cod or not nom or not prov_id:
            AlertaCustom.show_warning(self, "Campos Vacíos", "Código, Nombre y Proveedor son obligatorios.")
            return

        try:
            if self.producto_id:
                query = """UPDATE productos SET codigo=%s, nombre=%s, precio_compra=%s, precio_venta=%s, 
                           precio_mayoreo=%s, impuesto=%s, unidad_medida=%s, id_proveedor=%s WHERE id_producto=%s"""
                self.db.execute_query(query, (cod, nom, self.spin_compra.value(), self.spin_venta.value(), 
                                              self.spin_mayoreo.value(), self.spin_impuesto.value(), self.input_unidad.text(), prov_id, self.producto_id))
            else:
                query = """INSERT INTO productos (codigo, nombre, precio_compra, precio_venta, precio_mayoreo, impuesto, unidad_medida, id_proveedor, estatus)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)"""
                self.db.execute_query(query, (cod, nom, self.spin_compra.value(), self.spin_venta.value(), 
                                              self.spin_mayoreo.value(), self.spin_impuesto.value(), self.input_unidad.text(), prov_id))
            self.accept()
        except Exception as e:
            # Capturamos el error de código duplicado de PostgreSQL
            if "productos_codigo_key" in str(e):
                AlertaCustom.show_error(self, "Código Duplicado", "Ese código de artículo ya existe en el sistema.")
            else:
                AlertaCustom.show_error(self, "Error BD", f"Error al guardar producto: {e}")


class ModuloCatalogo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # Encabezado
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("GESTIÓN DE CATÁLOGO DE PRODUCTOS")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()

        self.btn_nuevo = BotonNuevo("Nuevo Producto")
        self.btn_nuevo.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px 20px;")
        self.btn_nuevo.clicked.connect(self.abrir_formulario)
        header_layout.addWidget(self.btn_nuevo)
        layout.addLayout(header_layout)

        # Buscador
        self.input_buscar = InputBuscador("Buscar por código o nombre...")
        self.input_buscar.textChanged.connect(self.cargar_tabla)
        layout.addWidget(self.input_buscar) # <-- Esto lo hace visible en pantalla

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels(["ID", "Código", "Nombre", "P. Compra", "P. Venta", "P. Mayoreo", "U. Medida", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID más chico
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabla)

        self.cargar_tabla()

    def cargar_tabla(self):
        filtro = f"%{self.input_buscar.text().strip()}%"
        query = """
            SELECT id_producto, codigo, nombre, precio_compra, precio_venta, precio_mayoreo, unidad_medida
            FROM productos 
            WHERE estatus = TRUE AND (codigo ILIKE %s OR nombre ILIKE %s)
            ORDER BY nombre ASC
        """
        try:
            resultados = self.db.fetch_all(query, (filtro, filtro))
            self.tabla.setRowCount(0)
            
            for i, fila in enumerate(resultados or []):
                self.tabla.insertRow(i)
                for j in range(7):
                    item = QTableWidgetItem(f"${fila[j]:,.2f}" if j in [3,4,5] else str(fila[j]))
                    self.tabla.setItem(i, j, item)
                
                # Botonera de acciones (Editar y Baja)
                btns = QWidget()
                ly = QHBoxLayout(btns)
                ly.setContentsMargins(0, 0, 0, 0)
                
                btn_edit = BotonEditar("Editar")
                btn_edit.setStyleSheet("background-color: #f39c12; color: white;")
                btn_edit.clicked.connect(lambda _, id_prod=fila[0]: self.abrir_formulario(id_prod))
                
                btn_baja = BotonBaja("Baja")
                btn_baja.setStyleSheet("background-color: #e74c3c; color: white;")
                btn_baja.clicked.connect(lambda _, id_prod=fila[0]: self.dar_de_baja(id_prod))
                
                ly.addWidget(btn_edit)
                ly.addWidget(btn_baja)
                self.tabla.setCellWidget(i, 7, btns)

        except Exception as e:
            print(f"Error cargando catálogo: {e}")

    def abrir_formulario(self, producto_id=None): # <-- 1. Le decimos que acepte un ID (por defecto None)
        # 2. Pasamos ese ID a la clase FormularioProducto
        modal = FormularioProducto(self.db, producto_id, parent=self) 
        if modal.exec():
            self.cargar_tabla()

    def dar_de_baja(self, id_producto):
        if AlertaCustom.ask_confirm(self, "Baja de Producto", "¿Estás seguro de desactivar este producto? Ya no aparecerá en el punto de venta."):
            self.db.execute_query("UPDATE productos SET estatus = FALSE WHERE id_producto = %s", (id_producto,))
            self.cargar_tabla()