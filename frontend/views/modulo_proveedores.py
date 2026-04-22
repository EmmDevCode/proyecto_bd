# frontend/views/modulo_proveedores.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidgetItem,
                             QDialog, QFormLayout)
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom
from frontend.components.elementos_ui import DataTable, BotonGuardar, BotonEditar, BotonNuevo, BotonBaja

class FormularioProveedor(QDialog):
    def __init__(self, db, proveedor_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.proveedor_id = proveedor_id
        self.init_ui()
        if self.proveedor_id: self.cargar_datos()

    def init_ui(self):
        self.setWindowTitle("Nuevo Proveedor" if not self.proveedor_id else "Editar Proveedor")
        self.setFixedWidth(400)
        layout = QFormLayout(self)
        self.input_nombre = QLineEdit()
        self.input_rfc = QLineEdit(); self.input_rfc.setMaxLength(13)
        self.input_telefono = QLineEdit(); self.input_telefono.setMaxLength(10)
        self.input_contacto = QLineEdit()
        layout.addRow("Razón Social:", self.input_nombre)
        layout.addRow("RFC:", self.input_rfc)
        layout.addRow("Teléfono:", self.input_telefono)
        layout.addRow("Persona Contacto:", self.input_contacto)
        btn_guardar = BotonGuardar("Guardar")
        btn_guardar.setStyleSheet("background-color: #f39c12; color: white; padding: 10px;")
        btn_guardar.clicked.connect(self.guardar)
        layout.addRow(btn_guardar)

    def cargar_datos(self):
        res = self.db.fetch_one("SELECT nombre, rfc, telefono, persona_contacto FROM proveedores WHERE id_proveedor = %s", (self.proveedor_id,))
        if res:
            self.input_nombre.setText(res[0]); self.input_rfc.setText(res[1])
            self.input_telefono.setText(res[2]); self.input_contacto.setText(res[3])

    def guardar(self):
        nom = self.input_nombre.text().strip()
        if not nom: return AlertaCustom.show_warning(self, "Aviso", "El nombre es obligatorio.")
        try:
            if self.proveedor_id:
                self.db.execute_query("UPDATE proveedores SET nombre=%s, rfc=%s, telefono=%s, persona_contacto=%s WHERE id_proveedor=%s", 
                                      (nom, self.input_rfc.text(), self.input_telefono.text(), self.input_contacto.text(), self.proveedor_id))
            else:
                self.db.execute_query("INSERT INTO proveedores (nombre, rfc, telefono, persona_contacto, estatus) VALUES (%s, %s, %s, %s, TRUE)", 
                                      (nom, self.input_rfc.text(), self.input_telefono.text(), self.input_contacto.text()))
            self.accept()
        except Exception as e: AlertaCustom.show_error(self, "Error", str(e))

class ModuloProveedores(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        header = QHBoxLayout()
        lbl = QLabel("DIRECTORIO DE PROVEEDORES"); lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        btn_nuevo = BotonNuevo("Registrar Proveedor"); btn_nuevo.setStyleSheet("background-color: #f39c12; color: white; padding: 10px;")
        btn_nuevo.clicked.connect(lambda: self.abrir_formulario())
        header.addWidget(lbl); header.addStretch(); header.addWidget(btn_nuevo)
        layout.addLayout(header)
        self.tabla = DataTable(["ID", "Nombre", "RFC", "Teléfono", "Contacto", "Acciones"])
        layout.addWidget(self.tabla)
        self.cargar_datos()

    def cargar_datos(self):
        res = self.db.fetch_all("SELECT id_proveedor, nombre, rfc, telefono, persona_contacto FROM proveedores WHERE estatus = TRUE ORDER BY nombre")
        self.tabla.setRowCount(0)
        for i, fila in enumerate(res or []):
            self.tabla.insertRow(i)
            for j in range(5): self.tabla.setItem(i, j, QTableWidgetItem(str(fila[j])))
            
            btns = QWidget()
            ly = QHBoxLayout(btns)
            ly.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = BotonEditar("Editar")
            btn_edit.setStyleSheet("background-color: #f39c12; color: white;")
            btn_edit.clicked.connect(lambda _, id_p=fila[0]: self.abrir_formulario(id_p))
            
            btn_del = BotonBaja("Baja")
            btn_del.setStyleSheet("background-color: #e74c3c; color: white;")
            btn_del.clicked.connect(lambda _, id_p=fila[0]: self.eliminar(id_p))
            
            ly.addWidget(btn_edit)
            ly.addWidget(btn_del)
            self.tabla.setCellWidget(i, 5, btns)

    def abrir_formulario(self, id_p=None):
        if FormularioProveedor(self.db, id_p, self).exec(): self.cargar_datos()

    def eliminar(self, id_p):
        if AlertaCustom.ask_confirm(self, "Baja", "¿Desactivar proveedor?"):
            self.db.execute_query("UPDATE proveedores SET estatus = FALSE WHERE id_proveedor = %s", (id_p,))
            self.cargar_datos()