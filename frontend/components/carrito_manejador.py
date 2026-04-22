# frontend/components/carrito_manager.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QAbstractItemView, QTableWidgetItem
from PyQt6.QtCore import Qt
from frontend.components.elementos_ui import DataTable

class CarritoManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.productos = [] # Lista interna de diccionarios
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. La Tabla del Carrito
        self.tabla = DataTable(["", "codigo", "Producto", "Cant.", "desc", "Precio U.", "Subtotal"])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.tabla.itemChanged.connect(self.recalcular_totales)
        layout.addWidget(self.tabla)

        # 2. El Totalizador
        footer = QHBoxLayout()
        footer.addStretch()
        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        footer.addWidget(self.lbl_total)
        layout.addLayout(footer)

    def agregar_producto(self, id_prod, codigo, nombre, precio):
        """Añade un producto nuevo al carrito (Ej. desde el escáner)"""
        self.productos.append({
            "id": id_prod, "codigo": codigo, "nombre": nombre, 
            "cant": 1.0, "desc": 0.0, 
            "precio": float(precio), "subtotal": float(precio)
        })
        self.refrescar_tabla()

    def cargar_carrito_existente(self, lista_productos):
        """Carga una lista de productos de golpe (Para el Modo Edición)"""
        self.productos = lista_productos
        self.refrescar_tabla()

    def bloquear_edicion(self):
        """Bloquea la tabla para el Modo Vista Previa"""
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def desbloquear_edicion(self):
        """Desbloquea la tabla para el Modo Edición"""
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)

    def refrescar_tabla(self):
        """Dibuja los items y bloquea las celdas que no son Cantidad ni Descuento"""
        self.tabla.blockSignals(True) 
        self.tabla.setRowCount(len(self.productos))
        
        total = 0.0
        for i, prod in enumerate(self.productos):
            items = [
                QTableWidgetItem(">"),
                QTableWidgetItem(prod['codigo']),
                QTableWidgetItem(prod['nombre']),
                QTableWidgetItem(str(prod['cant'])),   # Col 3: Cant
                QTableWidgetItem(str(prod['desc'])),   # Col 4: Desc
                QTableWidgetItem(f"{prod['precio']:.2f}"),
                QTableWidgetItem(f"{prod['subtotal']:.2f}")
            ]
            
            for col, item in enumerate(items):
                if col not in [3, 4]:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setBackground(Qt.GlobalColor.yellow) 
                self.tabla.setItem(i, col, item)
            
            total += prod['subtotal']
            
        self.lbl_total.setText(f"Total: ${total:.2f}")
        self.tabla.blockSignals(False)

    def recalcular_totales(self, item):
        """Se activa cuando el usuario edita la cantidad o descuento"""
        row = item.row()
        col = item.column()
        
        if col in [3, 4]: 
            try:
                nuevo_valor = float(item.text())
                if col == 3: self.productos[row]['cant'] = nuevo_valor
                elif col == 4: self.productos[row]['desc'] = nuevo_valor
                
                p = self.productos[row]
                self.productos[row]['subtotal'] = (p['precio'] * p['cant']) - p['desc']
                self.refrescar_tabla()
            except ValueError:
                pass 

    def obtener_datos(self):
        """Devuelve los productos y el total actual para guardarlos en BD"""
        total = sum(p['subtotal'] for p in self.productos)
        return self.productos, total