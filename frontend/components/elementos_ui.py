# frontend/components/ui_elements.py
from PyQt6.QtWidgets import QPushButton, QLineEdit, QTableWidget, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt
import qtawesome as qta

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

class BotonGuardar(QPushButton):
    def __init__(self, texto="Guardar", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.save', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white; 
                padding: 10px 20px; font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonEditar(QPushButton):
    def __init__(self, texto="Editar", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.pen', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #f39c12; color: white; 
                padding: 6px 12px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #f1c40f; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonBaja(QPushButton):
    def __init__(self, texto="Baja", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.trash', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white; 
                padding: 6px 12px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonNuevo(QPushButton):
    def __init__(self, texto="Nuevo Registro", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.plus', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; 
                padding: 10px 20px; font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonBuscar(QPushButton):
    def __init__(self, texto="Buscar", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.search', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6; color: white; 
                padding: 8px 15px; font-weight: bold; border-radius: 4px;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonConfirmar(QPushButton):
    """Botón grande para acciones principales como cobrar o confirmar compras"""
    def __init__(self, texto="Confirmar", parent=None):
        super().__init__(f"  {texto}", parent)
        # Usamos el icono de check-circle (o puedes usar 'fa5s.box' si prefieres la caja)
        self.setIcon(qta.icon('fa5s.check-circle', color='white'))
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white; 
                padding: 15px 20px; 
                font-weight: bold; 
                font-size: 14px; 
                border-radius: 6px;
            }
            QPushButton:hover { 
                background-color: #2ecc71; 
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BadgeEstado(QPushButton):
    """Etiqueta visual (Píldora) para mostrar estatus activo/inactivo"""
    def __init__(self, activo=True, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Para que no parezca botón al hacer clic
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) # Ignora el ratón
        
        if activo:
            self.setText("  Activo")
            self.setIcon(qta.icon('fa5s.check-circle', color='white'))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60; color: white;
                    border-radius: 12px; font-weight: bold; 
                    padding: 4px 10px; border: none; font-size: 11px;
                }
            """)
        else:
            self.setText("  Inactivo")
            self.setIcon(qta.icon('fa5s.times-circle', color='white'))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c; color: white;
                    border-radius: 12px; font-weight: bold; 
                    padding: 4px 10px; border: none; font-size: 11px;
                }
            """)

class BadgeBooleano(QPushButton):
    """Píldora para valores Sí/No (Ej. Precio Mayoreo)"""
    def __init__(self, activo=True, texto_v="Sí aplica", texto_f="No aplica", parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus) 
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
        
        if activo:
            self.setText(f"  {texto_v}")
            self.setIcon(qta.icon('fa5s.star', color='white')) # Icono de estrella para mayoreo
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3498db; color: white;
                    border-radius: 12px; font-weight: bold; 
                    padding: 4px 10px; border: none; font-size: 11px;
                }
            """)
        else:
            self.setText(f"  {texto_f}")
            self.setIcon(qta.icon('fa5s.minus', color='white'))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6; color: white;
                    border-radius: 12px; font-weight: bold; 
                    padding: 4px 10px; border: none; font-size: 11px;
                }
            """)

class BotonVerDetalles(QPushButton):
    """Botón para visualizar información extra (Caja, Historial, etc)"""
    def __init__(self, texto="Ver Detalles", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.eye', color='white')) # Icono de Ojo
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; 
                padding: 6px 12px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonImprimir(QPushButton):
    """Botón para imprimir o reimprimir tickets y cotizaciones"""
    def __init__(self, texto="Reimprimir Ticket", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.print', color='white')) # Icono de Impresora
        self.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white; 
                padding: 6px 12px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #732d91; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)