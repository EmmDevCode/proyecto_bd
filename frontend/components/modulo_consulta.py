# frontend/components/modulo_consulta.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QAbstractItemView, QTableWidgetItem, QMenu
from PyQt6.QtCore import Qt
import datetime

from frontend.components.elementos_ui import FormInput, DataTable
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom

class ModuloConsulta(QWidget):
    """
    Componente Universal para mostrar tablas con buscador.
    Se usa en Ventas, Cotizaciones, Caja, Inventario, etc.
    """
    def __init__(self, titulo, columnas, query_base, action_callback=None, menu_opciones=None, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.query_base = query_base
        self.columnas = columnas
        self.action_callback = action_callback # Función para doble clic
        self.menu_opciones = menu_opciones     # Diccionario para el clic derecho (Ej: {"Cobrar": funcion_cobrar})
        
        self.init_ui(titulo)
        self.cargar_datos_del_dia()

    def init_ui(self, titulo):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Cabecera y Buscador
        header = QHBoxLayout()
        self.lbl_titulo = QLabel(f"<b>{titulo}</b>")
        self.lbl_titulo.setStyleSheet("font-size: 18px; color: #2c3e50;")
        
        self.search_input = FormInput("🔍 Filtrar por folio o cliente...")
        self.search_input.setFixedWidth(350)
        self.search_input.textChanged.connect(self.filtrar_tabla)

        header.addWidget(self.lbl_titulo)
        header.addStretch()
        header.addWidget(self.search_input)
        layout.addLayout(header)

        # 2. La Tabla Reutilizable
        self.tabla = DataTable(self.columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Solo lectura
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Conectar eventos
        if self.action_callback:
            self.tabla.itemDoubleClicked.connect(self.gestionar_doble_clic)
            
        # Habilitar menú contextual (Clic derecho) si se enviaron opciones
        if self.menu_opciones:
            self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)
            
        layout.addWidget(self.tabla)

    def cargar_datos_del_dia(self):
        hoy = datetime.date.today()
        try:
            resultados = self.db.fetch_all(self.query_base, (hoy,))
            self.tabla.setRowCount(len(resultados))
            
            for i, fila in enumerate(resultados):
                for j, valor in enumerate(fila):
                    item = QTableWidgetItem(str(valor))
                    self.tabla.setItem(i, j, item)
        except Exception as e:
            print(f"Error cargando tabla: {e}")

    def filtrar_tabla(self, texto):
        for i in range(self.tabla.rowCount()):
            match = False
            for j in range(self.tabla.columnCount()):
                item = self.tabla.item(i, j)
                if item and texto.lower() in item.text().lower():
                    match = True
                    break
            self.tabla.setRowHidden(i, not match)

    def gestionar_doble_clic(self, item):
        """Dispara la función asignada enviando el Folio de la fila seleccionada"""
        row = item.row()
        folio = self.tabla.item(row, 0).text()
        
        # Validar estatus si existe la columna
        if "Estatus" in self.columnas:
            col_estatus = self.columnas.index("Estatus")
            estatus = self.tabla.item(row, col_estatus).text()
            if estatus == 'Cobrada':
                AlertaCustom.show_info(self, "Orden Bloqueada", f"El folio {folio} ya fue cobrado.")
                return

        self.action_callback(folio)

    def mostrar_menu_contextual(self, posicion):
        """Crea un menú de clic derecho dinámico"""
        item = self.tabla.itemAt(posicion)
        if not item: return

        row = item.row()
        folio = self.tabla.item(row, 0).text()

        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: white; border: 1px solid #bdc3c7; } QMenu::item { padding: 8px 20px; } QMenu::item:selected { background-color: #3498db; color: white; }")

        for nombre_accion, funcion_accion in self.menu_opciones.items():
            accion = menu.addAction(nombre_accion)
            # Usamos lambda para pasarle el folio a la función que la llamó
            accion.triggered.connect(lambda checked, f=folio, func=funcion_accion: func(f))

        menu.exec(self.tabla.viewport().mapToGlobal(posicion))