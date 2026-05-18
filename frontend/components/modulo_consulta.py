# frontend/components/modulo_consulta.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QAbstractItemView, QTableWidgetItem, QMenu, QLineEdit
from PyQt6.QtCore import Qt
import qtawesome as qta
import datetime

# ¡Importamos el FiltroFecha!
from frontend.components.elementos_ui import DataTable, BotonBuscar, FiltroFecha
from backend.bd_conexion import DatabaseConnection
from frontend.components.alertas import AlertaCustom


class ModuloConsulta(QWidget):
    """
    Componente Universal para mostrar tablas con buscador y filtro de fecha.
    """
    def __init__(self, titulo, columnas, query_base, action_callback=None, menu_opciones=None, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.query_base = query_base
        self.columnas = columnas
        self.action_callback = action_callback 
        self.menu_opciones = menu_opciones     
        
        self.init_ui(titulo)
        self.cargar_datos_del_dia()

    def init_ui(self, titulo):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Cabecera, Buscador y Calendario
        header = QHBoxLayout()
        self.lbl_titulo = QLabel(f"<b>{titulo}</b>")
        self.lbl_titulo.setStyleSheet("font-size: 18px; color: #2c3e50;")
        
        # --- NUEVO: FILTRO DE FECHA ---
        self.container_fecha = QWidget()
        ly_fecha = QHBoxLayout(self.container_fecha)
        ly_fecha.setContentsMargins(0,0,0,0)
        ly_fecha.setSpacing(5)

        # Icono de calendario en lugar de emoji
        self.icon_cal = QLabel()
        self.icon_cal.setPixmap(qta.icon('fa5s.calendar-alt', color='#7f8c8d').pixmap(18, 18))
        
        self.lbl_fecha_txt = QLabel("Fecha:")
        self.lbl_fecha_txt.setStyleSheet("font-size: 14px; font-weight: bold; color: #7f8c8d;")
        
        self.filtro_fecha = FiltroFecha()
        self.filtro_fecha.setFixedWidth(130)
        self.filtro_fecha.dateChanged.connect(self.cargar_datos_del_dia)
        
        ly_fecha.addWidget(self.icon_cal)
        ly_fecha.addWidget(self.lbl_fecha_txt)
        ly_fecha.addWidget(self.filtro_fecha)
        
        # MAGIA: Si la consulta SQL no usa fecha (no tiene '%s'), ocultamos el calendario
        if "%s" not in self.query_base:
            self.container_fecha.hide()
    

        # --- BUSCADOR DE TEXTO ---
        self.search_input = QLineEdit() 
        self.search_input.setPlaceholderText("Filtrar por folio o cliente...")
        self.search_input.setFixedWidth(350)
        self.search_input.setStyleSheet("padding: 8px 8px 8px 5px; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self.search_input.addAction(qta.icon('fa5s.search', color='#7f8c8d'), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self.filtrar_tabla)

        header.addWidget(self.lbl_titulo)
        header.addStretch()
        header.addWidget(self.container_fecha) # Añadimos el contenedor con el icono
        header.addSpacing(15)
        header.addWidget(self.search_input)
        layout.addLayout(header)

        # 2. La Tabla Reutilizable
        self.tabla = DataTable(self.columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Conectar eventos
        if self.action_callback:
            self.tabla.itemDoubleClicked.connect(self.gestionar_doble_clic)
            
        if self.menu_opciones:
            self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)
            
        layout.addWidget(self.tabla)

    def cargar_datos_del_dia(self):
        # Obtenemos la fecha que el usuario seleccionó en el QDateEdit
        qdate = self.filtro_fecha.date()
        fecha_str = qdate.toString("yyyy-MM-dd") # Formato exacto para PostgreSQL
        
        try:
            # Validamos si la query requiere la fecha o no
            if "%s" in self.query_base:
                resultados = self.db.fetch_all(self.query_base, (fecha_str,))
            else:
                resultados = self.db.fetch_all(self.query_base)

            self.tabla.setRowCount(len(resultados or []))
            
            for i, fila in enumerate(resultados or []):
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
        row = item.row()
        folio = self.tabla.item(row, 0).text()
        
        if "Estatus" in self.columnas:
            col_estatus = self.columnas.index("Estatus")
            estatus = self.tabla.item(row, col_estatus).text()
            if estatus == 'Cobrada':
                AlertaCustom.show_info(self, "Orden Bloqueada", f"El folio {folio} ya fue cobrado.")
                return

        self.action_callback(folio)

    def mostrar_menu_contextual(self, posicion):
        item = self.tabla.itemAt(posicion)
        if not item: return

        row = item.row()
        folio = self.tabla.item(row, 0).text()

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #bdc3c7; border-radius: 4px; } 
            QMenu::item { padding: 8px 30px 8px 20px; font-size: 13px; } 
            QMenu::item:selected { background-color: #3498db; color: white; }
        """)

        for nombre_accion, funcion_accion in self.menu_opciones.items():
            if "Cobrar" in nombre_accion:
                icono = qta.icon('fa5s.cash-register', color='#27ae60')
            elif "Detalles" in nombre_accion:
                icono = qta.icon('fa5s.eye', color='#3498db')
            elif "Reimprimir" in nombre_accion:
                icono = qta.icon('fa5s.print', color='#8e44ad')
            else:
                icono = qta.icon('fa5s.chevron-right', color='#7f8c8d')

            accion = menu.addAction(icono, nombre_accion)
            accion.triggered.connect(lambda checked, f=folio, func=funcion_accion: func(f))

        menu.exec(self.tabla.viewport().mapToGlobal(posicion))