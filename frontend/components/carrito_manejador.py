# frontend/components/carrito_manejador.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QAbstractItemView, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QSettings
from frontend.components.elementos_ui import DataTable

class CarritoManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.productos = [] 
        self.settings = QSettings("Ferrosoft", "PuntoDeVenta") 
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)


        self.tabla = DataTable(["Código", "Descripción", "U. Medida", "Cant.", "Desc. (%)", "Precio U.", "Importe"])
        
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | 
                                   QAbstractItemView.EditTrigger.AnyKeyPressed | 
                                   QAbstractItemView.EditTrigger.EditKeyPressed)
        
        self.tabla.setAlternatingRowColors(True) 
        self.tabla.setStyleSheet("""
            QTableWidget { font-size: 14px; gridline-color: #cbd5e1; selection-background-color: #bfdbfe; selection-color: black; }
            QHeaderView::section { font-weight: bold; background-color: #1e293b; color: white; padding: 5px; border: 1px solid #334155; }
        """)

        header = self.tabla.horizontalHeader()
        for i in range(self.tabla.columnCount()):
            width = self.settings.value(f"carrito_orden_col_{i}", None)
            if width:
                self.tabla.setColumnWidth(i, int(width))
            else:
                if i == 0: self.tabla.setColumnWidth(i, 130)
                elif i == 1: header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch) 
                elif i == 2: self.tabla.setColumnWidth(i, 90) # Ajuste para Unidad de Medida
                else: self.tabla.setColumnWidth(i, 110)
                
        header.sectionResized.connect(self.guardar_ancho_columnas)
        self.tabla.itemChanged.connect(self.recalcular_totales)
        layout.addWidget(self.tabla)

        self.lbl_total = QLabel("TOTAL: $0.00")
        self.lbl_total.setStyleSheet("""
            font-size: 28px; font-weight: 900; color: #0f172a; 
            padding: 0px 15px; background: transparent;
        """)

    def guardar_ancho_columnas(self, logicalIndex, oldSize, newSize):
        self.settings.setValue(f"carrito_orden_col_{logicalIndex}", newSize)

    def agregar_producto(self, id_prod, codigo, nombre, unidad, precio):
        self.productos.append({
            "id": id_prod, "codigo": codigo, "nombre": nombre, "unidad": unidad,
            "cant": 1.0, "desc": 0.0, 
            "precio": float(precio), "subtotal": float(precio)
        })
        self.refrescar_tabla()
        
        ultima_fila = len(self.productos) - 1
        self.tabla.setCurrentCell(ultima_fila, 3) 

    def cargar_carrito_existente(self, lista_productos):
        self.productos = lista_productos
        self.refrescar_tabla()

    def bloquear_edicion(self):
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def desbloquear_edicion(self):
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.AnyKeyPressed)

    def refrescar_tabla(self):
        self.tabla.blockSignals(True) 
        self.tabla.setRowCount(len(self.productos))
        
        total = 0.0
        for i, prod in enumerate(self.productos):
            items = [
                QTableWidgetItem(prod['codigo']),
                QTableWidgetItem(prod['nombre']),
                QTableWidgetItem(str(prod.get('unidad', 'PZA'))), 
                QTableWidgetItem(str(prod['cant'])),   
                QTableWidgetItem(str(prod['desc'])),   
                QTableWidgetItem(f"{prod['precio']:.2f}"),
                QTableWidgetItem(f"{prod['subtotal']:.2f}")
            ]
            
            for col, item in enumerate(items):
                # Ahora las editables son 3 (Cant) y 4 (Desc)
                if col not in [3, 4]:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setBackground(Qt.GlobalColor.yellow)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) 
                self.tabla.setItem(i, col, item)
            
            total += prod['subtotal']
            
        self.lbl_total.setText(f"TOTAL: ${total:,.2f}")
        self.tabla.blockSignals(False)

    def recalcular_totales(self, item):
        row = item.row()
        col = item.column()
        
       
        if col in [3, 4]: 
            try:
                nuevo_valor = float(item.text())
                if col == 3: self.productos[row]['cant'] = nuevo_valor
                elif col == 4: self.productos[row]['desc'] = nuevo_valor
                
                p = self.productos[row]
                
                subtotal_bruto = p['precio'] * p['cant']
                monto_descuento = subtotal_bruto * (p['desc'] / 100.0) 
                self.productos[row]['subtotal'] = subtotal_bruto - monto_descuento
                
                self.refrescar_tabla()
                self.tabla.setCurrentCell(row, col)
            except ValueError:
                pass 

    def obtener_datos(self):
        total = sum(p['subtotal'] for p in self.productos)
        return self.productos, total