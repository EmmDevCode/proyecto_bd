# frontend/views/modulo_clientes.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidgetItem,
                             QDialog, QFormLayout, QCheckBox)
from PyQt6.QtCore import Qt
import qtawesome as qta
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom
from frontend.components.elementos_ui import DataTable
from frontend.components.elementos_ui import BotonGuardar, BotonEditar, BotonBaja, BotonNuevo, BadgeBooleano


class FormularioCliente(QDialog):
    def __init__(self, db, cliente_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.cliente_id = cliente_id
        self.init_ui()
        if self.cliente_id: self.cargar_datos()

    def init_ui(self):
        self.setWindowTitle("Nuevo Cliente" if not self.cliente_id else "Editar Cliente")
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
        self.input_correo = QLineEdit(); self.input_correo.setStyleSheet(estilo_input)
        self.input_direccion = QLineEdit(); self.input_direccion.setStyleSheet(estilo_input)
        
        self.check_mayoreo = QCheckBox("Habilitar Precio de Mayoreo")
        self.check_mayoreo.setStyleSheet("QCheckBox { font-weight: bold; color: #475569; }")

        def crear_lbl(txt):
            l = QLabel(txt)
            l.setStyleSheet("font-weight: bold; color: #475569;")
            return l

        layout.addRow(crear_lbl("Nombre Completo:"), self.input_nombre)
        layout.addRow(crear_lbl("RFC:"), self.input_rfc)
        layout.addRow(crear_lbl("Teléfono:"), self.input_telefono)
        layout.addRow(crear_lbl("Correo:"), self.input_correo)
        layout.addRow(crear_lbl("Dirección:"), self.input_direccion)
        layout.addRow("", self.check_mayoreo)

        btn_layout = QHBoxLayout()
        btn_guardar = BotonGuardar("  Guardar Cliente")
        btn_guardar.setIcon(qta.icon('fa5s.save', color='white'))
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
        res = self.db.fetch_one("SELECT nombre_completo, rfc, telefono, correo, direccion, precio_mayoreo FROM clientes WHERE id_cliente = %s", (self.cliente_id,))
        if res:
            self.input_nombre.setText(res[0]); self.input_rfc.setText(res[1])
            self.input_telefono.setText(res[2]); self.input_correo.setText(res[3])
            self.input_direccion.setText(res[4]); self.check_mayoreo.setChecked(bool(res[5]))

    def guardar(self):
        nom, rfc = self.input_nombre.text().strip(), self.input_rfc.text().strip()
        if not nom: return AlertaCustom.show_warning(self, "Aviso", "El nombre es obligatorio.")
        try:
            if self.cliente_id:
                self.db.execute_query("UPDATE clientes SET nombre_completo=%s, rfc=%s, telefono=%s, correo=%s, direccion=%s, precio_mayoreo=%s WHERE id_cliente=%s", 
                                      (nom, rfc, self.input_telefono.text(), self.input_correo.text(), self.input_direccion.text(), self.check_mayoreo.isChecked(), self.cliente_id))
            else:
                self.db.execute_query("INSERT INTO clientes (nombre_completo, rfc, telefono, correo, direccion, precio_mayoreo, estatus) VALUES (%s, %s, %s, %s, %s, %s, TRUE)", 
                                      (nom, rfc, self.input_telefono.text(), self.input_correo.text(), self.input_direccion.text(), self.check_mayoreo.isChecked()))
            self.accept()
        except Exception as e: AlertaCustom.show_error(self, "Error", str(e))

class ModuloClientes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        header = QHBoxLayout()
        
        lbl_icono = QLabel()
        lbl_icono.setPixmap(qta.icon('fa5s.users', color='#3b82f6').pixmap(28, 28))
        header.addWidget(lbl_icono)
        
        lbl_titulo = QLabel("DIRECTORIO DE CLIENTES")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a;")
        header.addWidget(lbl_titulo)
        
        header.addStretch()
        
        self.btn_nuevo = BotonNuevo("  Registrar Cliente")
        self.btn_nuevo.setIcon(qta.icon('fa5s.user-plus', color='white'))
        self.btn_nuevo.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 12px 20px; border-radius: 8px; border: none;")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.clicked.connect(lambda: self.abrir_formulario())
        header.addWidget(self.btn_nuevo)
        
        layout.addLayout(header)
        self.tabla = DataTable(["ID", "Nombre", "RFC", "Teléfono", "Mayoreo", "Acciones"])
        layout.addWidget(self.tabla)
        self.cargar_datos()

    def cargar_datos(self):
        res = self.db.fetch_all("SELECT id_cliente, nombre_completo, rfc, telefono, precio_mayoreo FROM clientes WHERE estatus = TRUE ORDER BY nombre_completo")
        self.tabla.setRowCount(0)
        for i, fila in enumerate(res or []):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(str(fila[0])))
            self.tabla.setItem(i, 1, QTableWidgetItem(fila[1]))
            self.tabla.setItem(i, 2, QTableWidgetItem(fila[2]))
            self.tabla.setItem(i, 3, QTableWidgetItem(fila[3]))
            
            # --- COLUMNA 4: Píldora de Mayoreo ---
            badge = BadgeBooleano(activo=fila[4], texto_v="Mayoreo", texto_f="Normal")
            contenedor_badge = QWidget()
            ly_badge = QHBoxLayout(contenedor_badge)
            ly_badge.setContentsMargins(0, 0, 0, 0)
            ly_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ly_badge.addWidget(badge)
            self.tabla.setCellWidget(i, 4, contenedor_badge)
            
            # --- COLUMNA 5: Botones de Acción Limpios ---
            btns = QWidget()
            ly = QHBoxLayout(btns)
            ly.setContentsMargins(0, 0, 0, 0)
            
            
            btn_edit = BotonEditar("Editar")
            btn_edit.clicked.connect(lambda _, id_c=fila[0]: self.abrir_formulario(id_c))
            
            btn_del = BotonBaja("Baja")
            btn_del.clicked.connect(lambda _, id_c=fila[0]: self.eliminar(id_c))
            
            ly.addWidget(btn_edit)
            ly.addWidget(btn_del)
            self.tabla.setCellWidget(i, 5, btns)

    def abrir_formulario(self, id_c=None):
        if FormularioCliente(self.db, id_c, self).exec(): self.cargar_datos()

    def eliminar(self, id_c):
        if AlertaCustom.ask_confirm(self, "Baja", "¿Desactivar cliente?"):
            self.db.execute_query("UPDATE clientes SET estatus = FALSE WHERE id_cliente = %s", (id_c,))
            self.cargar_datos()