# frontend/components/ui_elements.py
from PyQt6.QtWidgets import QPushButton, QLineEdit, QTableWidget, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt

class PrimaryButton(QPushButton):
    """Botón principal para acciones positivas (Guardar, Cobrar, Nuevo)"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1c6ea4; }
        """)

class FormInput(QLineEdit):
    """Campo de texto estándar para formularios"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #3498db; }
        """)

class DataTable(QTableWidget):
    """Tabla estandarizada para mostrar registros (solo lectura por defecto)"""
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        
        # Comportamientos por defecto
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Solo lectura
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Seleccionar fila completa
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Ajustar al ancho
        self.verticalHeader().setVisible(False) # Ocultar números de fila laterales
        
        self.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                border: 1px solid #dcdde1;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
        """)