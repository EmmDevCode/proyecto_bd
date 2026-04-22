# frontend/views/modulo_almacenes.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidgetItem,
                             QHeaderView, QDialog, QFormLayout)
from PyQt6.QtCore import Qt
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom
from frontend.components.elementos_ui import DataTable

class FormularioAlmacen(QDialog):
    """Modal para Alta y Edición de Almacenes"""
    def __init__(self, db, almacen_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.almacen_id = almacen_id
        self.init_ui()
        if self.almacen_id:
            self.cargar_datos()

    def init_ui(self):
        self.setWindowTitle("Nuevo Almacén" if not self.almacen_id else "Editar Almacén")
        self.setFixedWidth(400)
        self.setStyleSheet("background-color: white; font-size: 14px;")
        
        layout = QFormLayout(self)
        layout.setSpacing(15)

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Ej. ALM-01")
        self.input_nombre = QLineEdit()
        self.input_responsable = QLineEdit()

        layout.addRow("Código:", self.input_codigo)
        layout.addRow("Nombre del Almacén:", self.input_nombre)
        layout.addRow("Responsable:", self.input_responsable)

        btn_layout = QHBoxLayout()
        btn_guardar = QPushButton("💾 Guardar Almacén")
        btn_guardar.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        btn_guardar.clicked.connect(self.guardar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #95a5a6; color: white; padding: 10px;")
        btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addRow(btn_layout)

    def cargar_datos(self):
        query = "SELECT codigo, nombre, responsable FROM almacenes WHERE id_almacen = %s"
        res = self.db.fetch_one(query, (self.almacen_id,))
        if res:
            self.input_codigo.setText(res[0])
            self.input_nombre.setText(res[1])
            self.input_responsable.setText(res[2])

    def guardar(self):
        cod = self.input_codigo.text().strip()
        nom = self.input_nombre.text().strip()
        resp = self.input_responsable.text().strip()

        if not cod or not nom:
            AlertaCustom.show_warning(self, "Campos Vacíos", "Código y Nombre son obligatorios.")
            return

        try:
            if self.almacen_id:
                query = "UPDATE almacenes SET codigo=%s, nombre=%s, responsable=%s WHERE id_almacen=%s"
                self.db.execute_query(query, (cod, nom, resp, self.almacen_id))
            else:
                query = "INSERT INTO almacenes (codigo, nombre, responsable, estatus) VALUES (%s, %s, %s, TRUE)"
                self.db.execute_query(query, (cod, nom, resp))
            self.accept()
        except Exception as e:
            AlertaCustom.show_error(self, "Error", str(e))

class ModuloAlmacenes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        header = QHBoxLayout()
        lbl_titulo = QLabel("GESTIÓN DE UBICACIONES Y ALMACENES")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        header.addWidget(lbl_titulo)
        header.addStretch()

        self.btn_nuevo = QPushButton("+ Registrar Almacén")
        self.btn_nuevo.setStyleSheet("background-color: #27ae60; color: white; padding: 10px 20px;")
        self.btn_nuevo.clicked.connect(lambda: self.abrir_formulario())
        header.addWidget(self.btn_nuevo)
        layout.addLayout(header)

        self.tabla = DataTable(["ID", "Código", "Nombre", "Responsable", "Acciones"])
        layout.addWidget(self.tabla)
        self.cargar_datos()

    def cargar_datos(self):
        query = "SELECT id_almacen, codigo, nombre, responsable FROM almacenes WHERE estatus = TRUE ORDER BY id_almacen ASC"
        resultados = self.db.fetch_all(query)
        self.tabla.setRowCount(0)
        for i, fila in enumerate(resultados or []):
            self.tabla.insertRow(i)
            for j in range(4):
                self.tabla.setItem(i, j, QTableWidgetItem(str(fila[j])))
            
            # Botonera de acciones
            btns = QWidget()
            ly = QHBoxLayout(btns); ly.setContentsMargins(0,0,0,0)
            
            btn_edit = QPushButton("✏️"); btn_edit.clicked.connect(lambda _, id_a=fila[0]: self.abrir_formulario(id_a))
            btn_del = QPushButton("🗑️"); btn_del.clicked.connect(lambda _, id_a=fila[0]: self.eliminar(id_a))
            
            ly.addWidget(btn_edit); ly.addWidget(btn_del)
            self.tabla.setCellWidget(i, 4, btns)

    def abrir_formulario(self, almacen_id=None):
        if FormularioAlmacen(self.db, almacen_id, self).exec():
            self.cargar_datos()

    def eliminar(self, almacen_id):
        if AlertaCustom.ask_confirm(self, "Baja de Almacén", "¿Desactivar esta ubicación? No se borrarán los datos históricos."):
            self.db.execute_query("UPDATE almacenes SET estatus = FALSE WHERE id_almacen = %s", (almacen_id,))
            self.cargar_datos()