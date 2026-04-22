# frontend/views/modulo_reportes.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt
from backend.bd_conexion import DatabaseConnection

class CardIndicador(QFrame):
    """Tarjeta visual para mostrar totales (Ventas, Ganancias, etc)"""
    def __init__(self, titulo, valor, color_borde):
        super().__init__()
        self.setStyleSheet(f"background-color: white; border-radius: 10px; border-left: 6px solid {color_borde};")
        self.setFixedWidth(250)
        ly = QVBoxLayout(self)
        lbl_t = QLabel(titulo); lbl_t.setStyleSheet("color: #7f8c8d; font-weight: bold; border: none;")
        self.lbl_v = QLabel(valor); self.lbl_v.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; border: none;")
        ly.addWidget(lbl_t); ly.addWidget(self.lbl_v)

class ModuloReportes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- 1. FILA DE TARJETAS (CARDS) ---
        fila_cards = QHBoxLayout()
        self.card_ventas = CardIndicador("VENTAS DEL MES", "$0.00", "#3498db")
        self.card_productos = CardIndicador("PRODUCTOS ACTIVOS", "0", "#27ae60")
        self.card_alertas = CardIndicador("ALERTAS DE STOCK", "0", "#e67e22")
        
        fila_cards.addWidget(self.card_ventas)
        fila_cards.addWidget(self.card_productos)
        fila_cards.addWidget(self.card_alertas)
        fila_cards.addStretch()
        layout.addLayout(fila_cards)

        # --- 2. ÁREA DE GRÁFICAS (Simuladas con Barras de Progreso Estilizadas) ---
        panel_graficas = QFrame()
        panel_graficas.setStyleSheet("background-color: white; border-radius: 10px; padding: 20px;")
        ly_g = QVBoxLayout(panel_graficas)
        ly_g.addWidget(QLabel("<b>🏆 TOP 5 PRODUCTOS MÁS VENDIDOS (Rendimiento)</b>"))
        
        self.contenedor_barras = QVBoxLayout()
        ly_g.addLayout(self.contenedor_barras)
        layout.addWidget(panel_graficas)

        layout.addStretch()
        self.actualizar_datos()

    def actualizar_datos(self):
        try:
            # Datos para las Cards
            v_mes = self.db.fetch_one("SELECT SUM(total) FROM orden_venta WHERE estatus='Cobrada' AND fecha > CURRENT_DATE - INTERVAL '30 days'")
            self.card_ventas.lbl_v.setText(f"${(v_mes[0] or 0):,.2f}")
            
            p_total = self.db.fetch_one("SELECT COUNT(*) FROM productos WHERE estatus=TRUE")
            self.card_productos.lbl_v.setText(str(p_total[0]))

            s_bajo = self.db.fetch_one("SELECT COUNT(*) FROM inventario_almacen WHERE cantidad_existente <= 5")
            self.card_alertas.lbl_v.setText(str(s_bajo[0]))

            # Datos para la Gráfica de Barras
            # Limpiamos barras anteriores
            while self.contenedor_barras.count():
                child = self.contenedor_barras.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            query_top = """
                SELECT p.nombre, SUM(d.cantidad) as total 
                FROM detalle_venta d JOIN productos p ON d.id_producto = p.id_producto
                GROUP BY p.nombre ORDER BY total DESC LIMIT 5
            """
            top_prods = self.db.fetch_all(query_top)
            max_ventas = top_prods[0][1] if top_prods else 1

            for nombre, cant in (top_prods or []):
                fila = QHBoxLayout()
                fila.addWidget(QLabel(f"{nombre[:20]}..."), stretch=1)
                bar = QProgressBar()
                bar.setMaximum(int(max_ventas))
                bar.setValue(int(cant))
                bar.setTextVisible(True)
                bar.setFormat(f"{cant} unid.")
                bar.setStyleSheet("""
                    QProgressBar { border: 1px solid #bdc3c7; border-radius: 5px; text-align: center; height: 20px; }
                    QProgressBar::chunk { background-color: #3498db; }
                """)
                fila.addWidget(bar, stretch=3)
                self.contenedor_barras.addLayout(fila)

        except Exception as e: print(f"Error reportes: {e}")