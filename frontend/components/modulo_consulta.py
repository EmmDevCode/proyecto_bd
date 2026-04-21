# frontend/components/modulo_consulta.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QAbstractItemView, QTableWidgetItem
from PyQt6.QtCore import Qt
from frontend.components.elementos_ui import FormInput, DataTable # Ajusta a 'ui_elements' si así se llama tu archivo
from backend.bd_conexion import DatabaseConnection
import datetime

class ModuloConsulta(QWidget):
    def __init__(self, titulo, columnas, query_base, on_edit_callback=None, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.query_base = query_base
        self.columnas = columnas
        self.on_edit_callback = on_edit_callback # Guardamos la función que abre la ventana
        self.init_ui(titulo)
        self.cargar_datos_del_dia()

    def init_ui(self, titulo):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Barra Superior: Título y Buscador
        header = QHBoxLayout()
        self.lbl_titulo = QLabel(f"<b>{titulo}</b>")
        self.lbl_titulo.setStyleSheet("font-size: 18px;")
        
        self.search_input = FormInput("🔍 Filtrar por folio o cliente...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.filtrar_tabla)

        header.addWidget(self.lbl_titulo)
        header.addStretch()
        header.addWidget(self.search_input)
        layout.addLayout(header)

        # Tabla Central
        self.tabla = DataTable(self.columnas)
        # BLOQUEO MAESTRO: Desactivamos la edición inline para que el doble clic no abra el cursor de texto
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Conectamos el doble clic a nuestra función
        self.tabla.itemDoubleClicked.connect(self.gestionar_doble_clic)
        layout.addWidget(self.tabla)

    def gestionar_doble_clic(self, item):
        row = item.row()
        # El folio siempre está en la primera columna (0)
        folio = self.tabla.item(row, 0).text()
        
        # Verificamos si la orden ya está cobrada (si existe la columna Estatus)
        estatus_col = self.tabla.columnCount() - 1
        estatus = self.tabla.item(row, estatus_col).text() if "Estatus" in self.columnas else "Pendiente"

        if estatus == 'Cobrada':
            QMessageBox.information(self, "Aviso", f"La orden {folio} ya fue cobrada y no puede modificarse.")
            return

        # Si no está cobrada, disparamos la función para abrir el editor
        if self.on_edit_callback:
            self.on_edit_callback(folio)

    def cargar_datos_del_dia(self):
        hoy = datetime.date.today()
        resultados = self.db.fetch_all(self.query_base, (hoy,))
        
        self.tabla.setRowCount(len(resultados))
        for i, fila in enumerate(resultados):
            for j, valor in enumerate(fila):
                item = QTableWidgetItem(str(valor))
                # Doble candado: Aseguramos que el item en sí no sea editable
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla.setItem(i, j, item)

    def filtrar_tabla(self, texto):
        for i in range(self.tabla.rowCount()):
            match = False
            for j in range(self.tabla.columnCount()):
                item = self.tabla.item(i, j)
                if item and texto.lower() in item.text().lower():
                    match = True
                    break
            self.tabla.setRowHidden(i, not match)