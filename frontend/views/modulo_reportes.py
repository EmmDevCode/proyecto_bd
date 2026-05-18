# frontend/views/modulo_reportes.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt
import qtawesome as qta
from backend.bd_conexion import DatabaseConnection

class CardIndicador(QFrame):
    """Tarjeta visual para mostrar totales (Ventas, Ganancias, etc)"""
    def __init__(self, titulo, valor, color_borde, icon_name):
        super().__init__()
        # Quitamos el borde izquierdo tosco y ponemos un shadow/card web
        self.setStyleSheet(f"background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; border-top: 4px solid {color_borde};")
        self.setFixedWidth(280)
        
        ly = QVBoxLayout(self)
        ly.setContentsMargins(20, 20, 20, 20)
        
        ly_header = QHBoxLayout()
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #64748b; font-weight: 800; font-size: 13px; border: none; letter-spacing: 0.5px;")
        
        lbl_icon = QLabel()
        lbl_icon.setPixmap(qta.icon(icon_name, color=color_borde).pixmap(24, 24))
        lbl_icon.setStyleSheet("border: none;")
        
        ly_header.addWidget(lbl_t)
        ly_header.addStretch()
        ly_header.addWidget(lbl_icon)
        
        self.lbl_v = QLabel(valor)
        self.lbl_v.setStyleSheet("font-size: 32px; font-weight: 900; color: #0f172a; border: none; margin-top: 10px;")
        
        ly.addLayout(ly_header)
        ly.addWidget(self.lbl_v)

class ModuloReportes(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- HEADER ---
        header = QHBoxLayout()
        lbl_icono = QLabel()
        lbl_icono.setPixmap(qta.icon('fa5s.chart-line', color='#0f172a').pixmap(28, 28))
        header.addWidget(lbl_icono)
        
        lbl_titulo = QLabel("DASHBOARD Y REPORTES")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: 900; color: #0f172a;")
        header.addWidget(lbl_titulo)
        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(10)

        # --- 1. FILA DE TARJETAS (CARDS) ---
        fila_cards = QHBoxLayout()
        fila_cards.setSpacing(20)
        self.card_ventas = CardIndicador("VENTAS DEL MES", "$0.00", "#3b82f6", "fa5s.wallet")
        self.card_productos = CardIndicador("PRODUCTOS ACTIVOS", "0", "#10b981", "fa5s.box-open")
        self.card_alertas = CardIndicador("ALERTAS DE STOCK", "0", "#f59e0b", "fa5s.exclamation-triangle")
        
        fila_cards.addWidget(self.card_ventas)
        fila_cards.addWidget(self.card_productos)
        fila_cards.addWidget(self.card_alertas)
        fila_cards.addStretch()
        layout.addLayout(fila_cards)
        layout.addSpacing(20)

        # --- 2. ÁREA DE GRÁFICAS (Simuladas con Barras de Progreso Estilizadas) ---
        panel_graficas = QFrame()
        panel_graficas.setStyleSheet("background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;")
        ly_g = QVBoxLayout(panel_graficas)
        ly_g.setContentsMargins(24, 24, 24, 24)
        ly_g.setSpacing(20)
        
        ly_tit_g = QHBoxLayout()
        icono_g = QLabel()
        icono_g.setPixmap(qta.icon('fa5s.trophy', color='#f59e0b').pixmap(20, 20))
        lbl_tit_g = QLabel("TOP 5 PRODUCTOS MÁS VENDIDOS (Rendimiento)")
        lbl_tit_g.setStyleSheet("font-size: 14px; font-weight: 800; color: #475569;")
        ly_tit_g.addWidget(icono_g)
        ly_tit_g.addWidget(lbl_tit_g)
        ly_tit_g.addStretch()
        
        ly_g.addLayout(ly_tit_g)
        
        self.contenedor_barras = QVBoxLayout()
        self.contenedor_barras.setSpacing(15)
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
                lbl_nombre = QLabel(f"{nombre[:25]}...")
                lbl_nombre.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
                fila.addWidget(lbl_nombre, stretch=2)
                
                bar = QProgressBar()
                bar.setMaximum(int(max_ventas))
                bar.setValue(int(cant))
                bar.setTextVisible(True)
                bar.setFormat(f"  {cant} unidades")
                bar.setStyleSheet("""
                    QProgressBar { border: none; background-color: #f1f5f9; border-radius: 8px; text-align: left; height: 24px; font-weight: bold; color: #ffffff; }
                    QProgressBar::chunk { background-color: #3b82f6; border-radius: 8px; }
                """)
                fila.addWidget(bar, stretch=5)
                self.contenedor_barras.addLayout(fila)

        except Exception as e: print(f"Error reportes: {e}")