# frontend/views/modulo_corte.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout, QGroupBox, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
import qtawesome as qta

from backend.bd_conexion import DatabaseConnection
from frontend.components.elementos_ui import BotonConfirmar
from frontend.components.alertas import AlertaCustom

class ModuloCorte(QWidget):
    """Pantalla para realizar el arqueo final y cerrar el turno del cajero"""
    def __init__(self, user_data, id_corte, fondo_inicial, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.id_corte = id_corte
        self.fondo_inicial = fondo_inicial
        self.db = DatabaseConnection()
        
        # Variables para almacenar lo que dice el sistema
        self.sistema_efectivo = 0.0
        self.sistema_tarjetas = 0.0
        self.sistema_transferencias = 0.0
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- TÍTULO ---
        lbl_titulo = QLabel("ARQUEO Y CORTE DE CAJA")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)
        layout.addSpacing(20)

        # --- CONTENEDOR PRINCIPAL DIVIDIDO EN 2 COLUMNAS ---
        h_layout = QHBoxLayout()
        
        # ==========================================
        # COLUMNA IZQUIERDA: Resumen del Sistema
        # ==========================================
        grupo_sistema = QGroupBox("1. Resumen del Sistema (Teórico)")
        grupo_sistema.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        ly_sistema = QFormLayout(grupo_sistema)
        ly_sistema.setContentsMargins(20, 30, 20, 20)
        ly_sistema.setVerticalSpacing(15)

        self.lbl_fondo = QLabel(f"$ {self.fondo_inicial:,.2f}")
        self.lbl_ventas_efe = QLabel("$ 0.00")
        self.lbl_ventas_tar = QLabel("$ 0.00")
        self.lbl_ventas_tra = QLabel("$ 0.00")
        
        # Estilo para las etiquetas de resumen
        estilo_lbl = "font-size: 16px; color: #34495e; font-weight: bold;"
        for lbl in [self.lbl_fondo, self.lbl_ventas_efe, self.lbl_ventas_tar, self.lbl_ventas_tra]:
            lbl.setStyleSheet(estilo_lbl)

        ly_sistema.addRow("Fondo Inicial (Apertura):", self.lbl_fondo)
        ly_sistema.addRow("Ventas en Efectivo:", self.lbl_ventas_efe)
        ly_sistema.addRow("Ventas con Tarjeta:", self.lbl_ventas_tar)
        ly_sistema.addRow("Transferencias:", self.lbl_ventas_tra)
        
        h_layout.addWidget(grupo_sistema)

        # ==========================================
        # COLUMNA DERECHA: Declaración del Cajero
        # ==========================================
        grupo_cajero = QGroupBox("2. Declaración Física (Arqueo)")
        grupo_cajero.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #3498db; border-radius: 4px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; color: #3498db; }")
        ly_cajero = QFormLayout(grupo_cajero)
        ly_cajero.setContentsMargins(20, 30, 20, 20)
        ly_cajero.setVerticalSpacing(15)

        validador = QDoubleValidator(0.00, 999999.99, 2)
        validador.setNotation(QDoubleValidator.Notation.StandardNotation)

        # Creación de Inputs con iconos
        self.inputs = {}
        campos = [
            ("billetes", "Billetes ($):", "fa5s.money-bill-wave", "#27ae60"),
            ("monedas", "Monedas ($):", "fa5s.coins", "#f39c12"),
            ("debito", "T. Débito (Váuchers):", "fa5s.credit-card", "#3498db"),
            ("credito", "T. Crédito (Váuchers):", "fa5s.credit-card", "#8e44ad"),
            ("transferencia", "Transferencias (SPEI):", "fa5s.mobile-alt", "#34495e")
        ]

        for clave, texto, icono, color in campos:
            inp = QLineEdit()
            inp.setPlaceholderText("0.00")
            inp.setValidator(validador)
            inp.setStyleSheet("padding: 6px; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px;")
            inp.addAction(qta.icon(icono, color=color), QLineEdit.ActionPosition.LeadingPosition)
            inp.textChanged.connect(self.calcular_diferencias)
            self.inputs[clave] = inp
            ly_cajero.addRow(texto, inp)

        h_layout.addWidget(grupo_cajero)
        layout.addLayout(h_layout)

        # ==========================================
        # RESULTADOS Y BOTÓN DE CIERRE
        # ==========================================
        self.lbl_resultado = QLabel("Diferencia Total: $ 0.00")
        self.lbl_resultado.setStyleSheet("font-size: 24px; font-weight: bold; color: #7f8c8d; margin-top: 20px;")
        self.lbl_resultado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_resultado)

        layout.addStretch()

        self.btn_cerrar = BotonConfirmar("CERRAR TURNO Y GUARDAR CORTE")
        self.btn_cerrar.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; padding: 12px; border-radius: 4px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #c0392b; }")
        self.btn_cerrar.clicked.connect(self.procesar_cierre)
        layout.addWidget(self.btn_cerrar)

    def cargar_totales(self):
        """Consulta la BD cruzando orden_venta con cobro_venta mediante id_venta"""
        
        # Hacemos un JOIN usando id_venta, que es la llave foránea correcta
        query = """
            SELECT c.metodo_pago, SUM(v.total) 
            FROM orden_venta v
            JOIN cobro_venta c ON v.id_venta = c.id_venta 
            WHERE v.fecha = CURRENT_DATE AND v.estatus = 'Cobrada'
            GROUP BY c.metodo_pago
        """
        
        try:
            resultados = self.db.fetch_all(query)
            # Reiniciamos a 0
            self.sistema_efectivo = 0.0
            self.sistema_tarjetas = 0.0
            self.sistema_transferencias = 0.0
            
            for fila in (resultados or []):
                metodo = fila[0].lower() if fila[0] else ""
                monto = float(fila[1])
                
                if "efectivo" in metodo:
                    self.sistema_efectivo += monto
                elif "tarjeta" in metodo or "débito" in metodo or "crédito" in metodo:
                    self.sistema_tarjetas += monto
                elif "transferencia" in metodo:
                    self.sistema_transferencias += monto

            # Actualizamos las etiquetas de la izquierda
            self.lbl_ventas_efe.setText(f"$ {self.sistema_efectivo:,.2f}")
            self.lbl_ventas_tar.setText(f"$ {self.sistema_tarjetas:,.2f}")
            self.lbl_ventas_tra.setText(f"$ {self.sistema_transferencias:,.2f}")
            
            self.calcular_diferencias()
            
        except Exception as e:
            print(f"Error cargando totales: {e}")

    def calcular_diferencias(self):
        """Cruza lo esperado vs lo capturado en tiempo real"""
        # Lo que debe haber (Total Teórico)
        total_esperado = self.fondo_inicial + self.sistema_efectivo + self.sistema_tarjetas + self.sistema_transferencias
        
        # Lo que el cajero declara (Total Físico)
        try:
            total_fisico = sum(float(inp.text() or 0) for inp in self.inputs.values())
        except ValueError:
            total_fisico = 0.0

        diferencia = total_fisico - total_esperado

        if diferencia == 0:
            self.lbl_resultado.setText("Caja Cuadrada: ¡Perfecto! $ 0.00")
            self.lbl_resultado.setStyleSheet("font-size: 24px; font-weight: bold; color: #27ae60; margin-top: 20px;")
        elif diferencia > 0:
            self.lbl_resultado.setText(f"Sobrante en Caja: +$ {diferencia:,.2f}")
            self.lbl_resultado.setStyleSheet("font-size: 24px; font-weight: bold; color: #f39c12; margin-top: 20px;")
        else:
            self.lbl_resultado.setText(f"Faltante en Caja: -$ {abs(diferencia):,.2f}")
            self.lbl_resultado.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c; margin-top: 20px;")

    def procesar_cierre(self):
        """Guarda todo en la BD y cierra el turno"""
        if not self.id_corte:
            AlertaCustom.show_error(self, "Error", "No hay un turno abierto válido.")
            return

        try:
            valores = {k: float(inp.text() or 0) for k, inp in self.inputs.items()}
            total_declarado = sum(valores.values())
        except ValueError:
            AlertaCustom.show_error(self, "Error", "Verifica los montos ingresados.")
            return

        query = """
            UPDATE cortes_caja 
            SET fecha_hora_cierre = CURRENT_TIMESTAMP,
                cierre_billetes = %s,
                cierre_monedas = %s,
                cierre_debito = %s,
                cierre_credito = %s,
                cierre_transferencia = %s,
                total_calculado = %s,
                total_declarado = %s,
                estatus = 'Cerrada'
            WHERE id_corte = %s
        """
        
        # Calculamos el total teórico general para guardarlo
        total_calculado = self.fondo_inicial + self.sistema_efectivo + self.sistema_tarjetas + self.sistema_transferencias
        
        parametros = (
            valores["billetes"], valores["monedas"], valores["debito"], 
            valores["credito"], valores["transferencia"], 
            total_calculado, total_declarado, self.id_corte
        )

        try:
            self.db.execute_query(query, parametros)
            AlertaCustom.show_info(self, "Corte Exitoso", "El turno se ha cerrado y el arqueo ha sido guardado.")
            # Emitir señal o llamar función para cerrar la aplicación del cajero
            self.window().close() 
        except Exception as e:
            AlertaCustom.show_error(self, "Error BD", f"No se pudo guardar el corte: {str(e)}")