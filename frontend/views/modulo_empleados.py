# frontend/views/modulo_empleados.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTableWidgetItem,
                             QDialog, QFormLayout, QComboBox)
from PyQt6.QtCore import Qt
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom
from frontend.components.elementos_ui import DataTable, BotonNuevo, BotonGuardar, BotonEditar, BadgeEstado, BotonBaja

class FormularioEmpleado(QDialog):
    def __init__(self, db, empleado_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.empleado_id = empleado_id
        self.init_ui()
        if self.empleado_id: self.cargar_datos()

    def init_ui(self):
        self.setWindowTitle("Nuevo Empleado" if not self.empleado_id else "Editar Empleado")
        self.setFixedWidth(400)
        self.setStyleSheet("background-color: white; font-size: 14px;")
        layout = QFormLayout(self)
        
        self.input_nombre = QLineEdit()
        self.input_usuario = QLineEdit()
        self.input_pin = QLineEdit(); self.input_pin.setMaxLength(4)
        self.input_pin.setPlaceholderText("PIN de 4 dígitos")
        
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["vendedor", "caja", "admin"])

        layout.addRow("Nombre Completo:", self.input_nombre)
        layout.addRow("Usuario Acceso:", self.input_usuario)
        layout.addRow("PIN de Seguridad:", self.input_pin)
        layout.addRow("Rol del Sistema:", self.combo_rol)

        btn_guardar = BotonGuardar("Guardar Empleado")
        btn_guardar.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        btn_guardar.clicked.connect(self.guardar)
        layout.addRow(btn_guardar)

    def cargar_datos(self):
        res = self.db.fetch_one("SELECT nombre_completo, usuario, pin, rol FROM empleados WHERE id_empleado = %s", (self.empleado_id,))
        if res:
            self.input_nombre.setText(res[0]); self.input_usuario.setText(res[1])
            self.input_pin.setText(res[2])
            self.combo_rol.setCurrentText(res[3])

    def guardar(self):
        nom = self.input_nombre.text().strip()
        usu = self.input_usuario.text().strip()
        pin = self.input_pin.text().strip()
        rol = self.combo_rol.currentText()

        if not nom or not usu or len(pin) < 4:
            AlertaCustom.show_warning(self, "Aviso", "Todos los campos son obligatorios. El PIN debe ser de 4 dígitos.")
            return

        try:
            if self.empleado_id:
                self.db.execute_query("UPDATE empleados SET nombre_completo=%s, usuario=%s, pin=%s, rol=%s WHERE id_empleado=%s", 
                                      (nom, usu, pin, rol, self.empleado_id))
            else:
                self.db.execute_query("INSERT INTO empleados (nombre_completo, usuario, pin, rol, estatus) VALUES (%s, %s, %s, %s, TRUE)", 
                                      (nom, usu, pin, rol))
            self.accept()
        except Exception as e: AlertaCustom.show_error(self, "Error", str(e))

class ModuloEmpleados(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        header = QHBoxLayout()
        lbl = QLabel("GESTIÓN DE PERSONAL"); lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        btn_nuevo = BotonNuevo("Alta de Empleado"); btn_nuevo.setStyleSheet("background-color: #8e44ad; color: white; padding: 10px;")
        btn_nuevo.clicked.connect(lambda: self.abrir_formulario())
        header.addWidget(lbl); header.addStretch(); header.addWidget(btn_nuevo)
        layout.addLayout(header)

        self.tabla = DataTable(["ID", "Nombre", "Usuario", "Rol", "Estatus", "Acciones"])
        layout.addWidget(self.tabla)
        self.cargar_datos()

    def cargar_datos(self):
        res = self.db.fetch_all("SELECT id_empleado, nombre_completo, usuario, rol, estatus FROM empleados WHERE estatus = TRUE ORDER BY id_empleado")
        self.tabla.setRowCount(0)
        for i, fila in enumerate(res or []):
            self.tabla.insertRow(i)
            
            # Llenar las primeras 4 columnas con texto normal (ID, Nombre, Usuario, Rol)
            for j in range(4): 
                self.tabla.setItem(i, j, QTableWidgetItem(str(fila[j])))
            
            # Columna 4: Estatus (Usamos nuestro nuevo Badge)
            badge = BadgeEstado(activo=True)
            contenedor_badge = QWidget()
            ly_badge = QHBoxLayout(contenedor_badge)
            ly_badge.setContentsMargins(0, 0, 0, 0)
            ly_badge.setAlignment(Qt.AlignmentFlag.AlignCenter) # Lo centramos
            ly_badge.addWidget(badge)
            self.tabla.setCellWidget(i, 4, contenedor_badge)
            
            # Columna 5: Acciones (Tus botones reutilizables)
            btns = QWidget()
            ly = QHBoxLayout(btns)
            ly.setContentsMargins(0, 0, 0, 0)
            
            btn_edit = BotonEditar("Editar")
            btn_edit.clicked.connect(lambda _, id_e=fila[0]: self.abrir_formulario(id_e))
            
            btn_del = BotonBaja("Eliminar")
            btn_del.clicked.connect(lambda _, id_e=fila[0]: self.eliminar(id_e))
            
            ly.addWidget(btn_edit)
            ly.addWidget(btn_del)
            self.tabla.setCellWidget(i, 5, btns)

    def abrir_formulario(self, id_e=None):
        if FormularioEmpleado(self.db, id_e, self).exec(): self.cargar_datos()

    def eliminar(self, id_e):
        if AlertaCustom.ask_confirm(self, "Baja", "¿Desactivar el acceso de este empleado?"):
            self.db.execute_query("UPDATE empleados SET estatus = FALSE WHERE id_empleado = %s", (id_e,))
            self.cargar_datos()