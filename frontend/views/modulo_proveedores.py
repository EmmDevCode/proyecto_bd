# frontend/views/modulo_proveedores.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidgetItem,
                             QDialog, QFormLayout)
from PyQt6.QtCore import Qt
import qtawesome as qta
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
        self.setFixedWidth(480)
        self.setStyleSheet("background-color: #f8fafc; font-size: 14px;")
        
        layout = QFormLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        estilo_input = """
            QLineEdit { border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px; background-color: white; color: #1e293b; }
            QLineEdit:focus { border: 2px solid #3b82f6; }
        """
        
        self.input_nombre = QLineEdit(); self.input_nombre.setStyleSheet(estilo_input)
        self.input_rfc = QLineEdit(); self.input_rfc.setMaxLength(13); self.input_rfc.setStyleSheet(estilo_input)
        self.input_telefono = QLineEdit(); self.input_telefono.setMaxLength(10); self.input_telefono.setStyleSheet(estilo_input)
        self.input_contacto = QLineEdit(); self.input_contacto.setStyleSheet(estilo_input)
        
        def crear_lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet("font-weight: bold; color: #475569;")
            return l

        layout.addRow(crear_lbl("Razón Social:"), self.input_nombre)
        layout.addRow(crear_lbl("RFC:"), self.input_rfc)
        layout.addRow(crear_lbl("Teléfono:"), self.input_telefono)
        layout.addRow(crear_lbl("Persona Contacto:"), self.input_contacto)
        
        btn_layout = QHBoxLayout()
        btn_guardar = BotonGuardar("  Guardar Proveedor")
        btn_guardar.setIcon(qta.icon('fa5s.save', color='white'))
        btn_guardar.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 12px; border-radius: 8px; border: none;")
        btn_guardar.clicked.connect(self.guardar)
        
        btn_cancelar = QPushButton("  Cancelar")
        btn_cancelar.setIcon(qta.icon('fa5s.times', color='#64748b'))
        btn_cancelar.setStyleSheet("""
            QPushButton { background-color: transparent; color: #64748b; padding: 10px; font-weight: bold; border: 2px solid #e2e8f0; border-radius: 8px; }
            QPushButton:hover { background-color: #f1f5f9; color: #334155; border: 2px solid #cbd5e1; }
        """)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        layout.addRow(btn_layout)

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
        
        lbl_icono = QLabel()
        lbl_icono.setPixmap(qta.icon('fa5s.truck', color='#f59e0b').pixmap(28, 28))
        header.addWidget(lbl_icono)
        
        lbl_titulo = QLabel("DIRECTORIO DE PROVEEDORES")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a;")
        header.addWidget(lbl_titulo)
        
        header.addStretch()
        
        self.btn_nuevo = BotonNuevo("  Registrar Proveedor")
        self.btn_nuevo.setIcon(qta.icon('fa5s.plus', color='white'))
        self.btn_nuevo.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 12px 20px; border-radius: 8px; border: none;")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.clicked.connect(lambda: self.abrir_formulario())
        header.addWidget(self.btn_nuevo)
        
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
            btn_edit.clicked.connect(lambda _, id_p=fila[0]: self.abrir_formulario(id_p))
            
            btn_del = BotonBaja("Baja")
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