# frontend/components/search_modal.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt
from frontend.components.elementos_ui import FormInput, DataTable

class GenericSearchModal(QDialog):
    """
    Modal genérico para buscar registros en la base de datos.
    Totalmente reutilizable para Productos, Clientes, Proveedores, etc.
    """
    def __init__(self, title, placeholder, headers, query_function, parent=None):
        super().__init__(parent)
        self.title = title
        self.placeholder = placeholder
        self.headers = headers
        self.query_function = query_function
        self.selected_data = None # Aquí se guardará la fila que el usuario elija
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.resize(800, 500)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        # 1. Buscador Superior
        self.search_input = FormInput(self.placeholder)
        self.search_input.setStyleSheet("""
            QLineEdit { 
                background-color: #f8fafc; 
                border: 2px solid #e2e8f0; 
                border-radius: 8px; 
                padding: 12px 16px; 
                font-size: 14px; 
                color: #334155;
            }
            QLineEdit:focus { 
                border: 2px solid #3b82f6; 
                background-color: #ffffff; 
            }
        """)
        self.search_input.textChanged.connect(self.perform_search)
        layout.addWidget(self.search_input)

        # 2. Tabla Central (Usando tu componente reutilizable)
        self.table = DataTable(self.headers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px;")
        # Conectar el doble clic para seleccionar
        self.table.itemDoubleClicked.connect(self.select_item)
        layout.addWidget(self.table)

        # 3. Footer de Resultados
        self.lbl_registros = QLabel("0 Registros encontrados")
        self.lbl_registros.setStyleSheet("""
            background-color: #f1f5f9; 
            color: #64748b; 
            padding: 10px 16px; 
            font-weight: bold; 
            font-size: 13px; 
            border-radius: 6px;
        """)
        self.lbl_registros.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_registros)

        self.search_input.setFocus()

    def perform_search(self, text):
        """Ejecuta la búsqueda y llena la tabla"""
        # Si el texto está vacío o tiene menos de 2 letras, limpiamos la tabla y NO buscamos en la BD
        if len(text) < 2:
            self.table.setRowCount(0)
            self.lbl_registros.setText("0 Registros encontrados")
            return 

        resultados = self.query_function(text)
        
        self.table.setRowCount(len(resultados))
        for i, row_data in enumerate(resultados):
            for j, val in enumerate(row_data):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        
        self.lbl_registros.setText(f"{len(resultados)} Registros encontrados")

    def select_item(self):
        """Extrae los datos de la fila seleccionada y cierra el modal"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.selected_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(current_row, col)
                self.selected_data.append(item.text() if item else "")
            
            self.accept() # Cierra el diálogo y retorna éxito