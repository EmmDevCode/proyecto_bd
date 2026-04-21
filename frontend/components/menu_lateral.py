# frontend/components/sidebar.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class Sidebar(QFrame):
    def __init__(self, titulo, opciones, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        # Estilo basado en tus requerimientos de tema claro/oscuro profesional
        self.setStyleSheet("background-color: #2c3e50; color: white;")
        self.layout = QVBoxLayout(self)
        self.botones = {}
        self.init_ui(titulo, opciones)

    def init_ui(self, titulo, opciones):
        # Logo o Título del Módulo
        lbl_brand = QLabel(titulo)
        lbl_brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_brand.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px 0;")
        self.layout.addWidget(lbl_brand)

        # Creación dinámica de botones
        for nombre, callback in opciones.items():
            btn = QPushButton(nombre)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent; color: #ecf0f1;
                    text-align: left; padding: 15px; font-size: 14px; border-radius: 0;
                    border-left: 4px solid transparent;
                }
                QPushButton:hover { background-color: #34495e; border-left: 4px solid #3498db; }
            """)
            btn.clicked.connect(callback)
            self.layout.addWidget(btn)
            self.botones[nombre] = btn
        
        self.layout.addStretch()

    def resaltar_boton(self, nombre_activo):
        """Cambia el estilo del botón para indicar en qué sección estamos"""
        for nombre, btn in self.botones.items():
            if nombre == nombre_activo:
                btn.setStyleSheet("background-color: #34495e; color: white; text-align: left; padding: 15px; font-size: 14px; border-left: 4px solid #3498db;")
            else:
                btn.setStyleSheet("background-color: transparent; color: #ecf0f1; text-align: left; padding: 15px; font-size: 14px; border-left: 4px solid transparent;")