# frontend/components/ui_elements.py
from PyQt6.QtWidgets import QPushButton, QLineEdit, QTableWidget, QHeaderView, QAbstractItemView, QDateEdit
from PyQt6.QtCore import Qt, QDate
import qtawesome as qta

class PrimaryButton(QPushButton):
    """Botón principal para acciones positivas (Guardar, Cobrar, Nuevo)"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 10px 18px;
                border: none;
                border-radius: 6px;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
        """)

class FormInput(QLineEdit):
    """Campo de texto estándar para formularios"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                background-color: #f8fafc;
                font-size: 13px;
                color: #334155;
            }
            QLineEdit:focus { 
                border: 2px solid #3b82f6; 
                background-color: #ffffff; 
            }
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
                alternate-background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #475569;
                padding: 8px;
                border: none;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
                font-weight: 800;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: #e0f2fe;
                color: #0369a1;
            }
        """)

class BotonGuardar(QPushButton):
    def __init__(self, texto="Guardar", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.save', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: white; 
                padding: 10px 20px; font-weight: 700; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonEditar(QPushButton):
    def __init__(self, texto="Editar", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.pen', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b; color: white; 
                padding: 8px 16px; border-radius: 6px; font-weight: 700; border: none;
            }
            QPushButton:hover { background-color: #d97706; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonBaja(QPushButton):
    def __init__(self, texto="Baja", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.trash', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #ef4444; color: white; 
                padding: 8px 16px; border-radius: 6px; font-weight: 700; border: none;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonNuevo(QPushButton):
    def __init__(self, texto="Nuevo Registro", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.plus', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white; 
                padding: 10px 20px; font-weight: 700; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonBuscar(QPushButton):
    def __init__(self, texto="Buscar", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.search', color='white'))
        self.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6; color: white; 
                padding: 8px 16px; font-weight: 700; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class InputBuscador(QLineEdit):
    """Barra de búsqueda estandarizada con lupa vectorial incrustada (Para escribir)"""
    def __init__(self, placeholder="Buscar...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedWidth(350)
        self.setStyleSheet("""
            QLineEdit {
                padding: 10px 10px 10px 8px; 
                font-size: 14px; 
                border: 2px solid #e2e8f0; 
                border-radius: 8px;
                background-color: #f8fafc;
                color: #334155;
            }
            QLineEdit:focus { 
                border: 2px solid #3b82f6; 
                background-color: #ffffff; 
            }
        """)
        # Inyecta la lupa del lado izquierdo de la caja de texto
        self.addAction(qta.icon('fa5s.search', color='#7f8c8d'), QLineEdit.ActionPosition.LeadingPosition)

class BotonConfirmar(QPushButton):
    """Botón grande para acciones principales como cobrar o confirmar compras"""
    def __init__(self, texto="Confirmar", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.check-circle', color='white'))
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #10b981; 
                color: white; 
                padding: 14px 24px; 
                font-weight: 800; 
                font-size: 14px; 
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { 
                background-color: #059669; 
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
                    background-color: #10b981; color: white;
                    border-radius: 12px; font-weight: 700; 
                    padding: 6px 12px; border: none; font-size: 11px;
                }
            """)
        else:
            self.setText("  Inactivo")
            self.setIcon(qta.icon('fa5s.times-circle', color='white'))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444; color: white;
                    border-radius: 12px; font-weight: 700; 
                    padding: 6px 12px; border: none; font-size: 11px;
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
            self.setIcon(qta.icon('fa5s.star', color='white'))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6; color: white;
                    border-radius: 12px; font-weight: 700; 
                    padding: 6px 12px; border: none; font-size: 11px;
                }
            """)
        else:
            self.setText(f"  {texto_f}")
            self.setIcon(qta.icon('fa5s.minus', color='white'))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #94a3b8; color: white;
                    border-radius: 12px; font-weight: 700; 
                    padding: 6px 12px; border: none; font-size: 11px;
                }
            """)

class BotonVerDetalles(QPushButton):
    """Botón para visualizar información extra (Caja, Historial, etc)"""
    def __init__(self, texto="Ver Detalles", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.eye', color='white')) 
        self.setStyleSheet("""
            QPushButton {
                background-color: #0ea5e9; color: white; 
                padding: 8px 16px; border-radius: 6px; font-weight: 700; border: none;
            }
            QPushButton:hover { background-color: #0284c7; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class BotonImprimir(QPushButton):
    """Botón para imprimir o reimprimir tickets y cotizaciones"""
    def __init__(self, texto="Reimprimir Ticket", parent=None):
        super().__init__(f"  {texto}", parent)
        self.setIcon(qta.icon('fa5s.print', color='white')) 
        self.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6; color: white; 
                padding: 8px 16px; border-radius: 6px; font-weight: 700; border: none;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class FiltroFecha(QDateEdit):
    """Selector de fecha con calendario desplegable estilo corporativo"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True) # Activa el mini calendario flotante
        self.setDate(QDate.currentDate()) # Por defecto, muestra el día de hoy
        self.setDisplayFormat("dd/MM/yyyy")
        self.setStyleSheet("""
            QDateEdit {
                padding: 10px 12px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                background-color: #f8fafc;
                font-size: 14px;
                color: #334155;
                font-weight: 700;
            }
            QDateEdit:focus { 
                border: 2px solid #3b82f6; 
                background-color: #ffffff; 
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #e2e8f0;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)