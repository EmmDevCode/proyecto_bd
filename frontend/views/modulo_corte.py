# frontend/views/modulo_corte.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QGridLayout, QFrame)
from PyQt6.QtCore import Qt
import datetime

from frontend.components.elementos_ui import PrimaryButton
from frontend.components.alertas import AlertaCustom
from backend.bd_conexion import DatabaseConnection

class ModuloCorte(QWidget):
    def __init__(self, user_data, id_corte, fondo_inicial, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.id_corte = id_corte
        self.fondo_caja = fondo_inicial # Dinero real sacado de BD
        self.db = DatabaseConnection()
        
        self.total_efectivo_sistema = 0.0
        self.total_tarjeta = 0.0
        self.total_transferencia = 0.0
        self.fecha_apertura = None

        res = self.db.fetch_one("SELECT fecha_hora_apertura FROM cortes_caja WHERE id_corte = %s", (self.id_corte,))
        if res: self.fecha_apertura = res[0]
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # 1. TÍTULO Y FECHA
        header = QHBoxLayout()
        lbl_titulo = QLabel("<b>CORTE DE CAJA - TURNO ACTUAL</b>")
        lbl_titulo.setStyleSheet("font-size: 22px; color: #2c3e50;")
        
        lbl_fecha = QLabel(f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')} | Cajero: {self.user_data['nombre']}")
        lbl_fecha.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        
        header.addWidget(lbl_titulo)
        header.addStretch()
        header.addWidget(lbl_fecha)
        layout.addLayout(header)

        # 2. TARJETAS DE RESUMEN (INGRESOS DEL SISTEMA)
        grid_resumen = QGridLayout()
        
        self.card_efectivo = self.crear_tarjeta("Efectivo Registrado", "$0.00", "#27ae60")
        self.card_tarjeta = self.crear_tarjeta("Tarjetas (Débito/Crédito)", "$0.00", "#3498db")
        self.card_transferencia = self.crear_tarjeta("Transferencias", "$0.00", "#9b59b6")
        
        grid_resumen.addWidget(self.card_efectivo['frame'], 0, 0)
        grid_resumen.addWidget(self.card_tarjeta['frame'], 0, 1)
        grid_resumen.addWidget(self.card_transferencia['frame'], 0, 2)
        layout.addLayout(grid_resumen)

        # 3. ÁREA DE CUADRE (EL EFECTIVO FÍSICO)
        panel_cuadre = QFrame()
        panel_cuadre.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #dcdde1;")
        layout_cuadre = QVBoxLayout(panel_cuadre)
        
        layout_cuadre.addWidget(QLabel("<b>ARQUEO DE CAJA (Efectivo Físico)</b>"))
        
        grid_arqueo = QGridLayout()
        grid_arqueo.setSpacing(15)
        
        grid_arqueo.addWidget(QLabel("Efectivo Esperado (Sistema + Fondo):"), 0, 0)
        self.lbl_esperado = QLabel("$0.00")
        self.lbl_esperado.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        grid_arqueo.addWidget(self.lbl_esperado, 0, 1)

        grid_arqueo.addWidget(QLabel("<b>Efectivo Físico Contado:</b>"), 1, 0)
        self.input_fisico = QLineEdit()
        self.input_fisico.setPlaceholderText("Ingresa el dinero que tienes en cajón...")
        self.input_fisico.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px; border: 2px solid #bdc3c7; border-radius: 5px;")
        self.input_fisico.textChanged.connect(self.calcular_diferencia)
        grid_arqueo.addWidget(self.input_fisico, 1, 1)

        grid_arqueo.addWidget(QLabel("Diferencia:"), 2, 0)
        self.lbl_diferencia = QLabel("$0.00 (Cuadrado)")
        self.lbl_diferencia.setStyleSheet("font-size: 24px; font-weight: bold; color: #7f8c8d;")
        grid_arqueo.addWidget(self.lbl_diferencia, 2, 1)

        layout_cuadre.addLayout(grid_arqueo)
        layout.addWidget(panel_cuadre)

        layout.addStretch()

        # 4. BOTONERA FINAL
        footer = QHBoxLayout()
        self.btn_imprimir = PrimaryButton("🖨️ Imprimir y Cerrar Turno")
        self.btn_imprimir.setStyleSheet("background-color: #e67e22; padding: 15px; font-size: 16px;")
        self.btn_imprimir.clicked.connect(self.cerrar_turno)
        
        footer.addStretch()
        footer.addWidget(self.btn_imprimir)
        layout.addLayout(footer)

    def crear_tarjeta(self, titulo, valor_inicial, color_borde):
        """Crea un widget de estilo 'Card' para los indicadores"""
        frame = QFrame()
        frame.setStyleSheet(f"background-color: white; border-radius: 8px; border-left: 5px solid {color_borde}; padding: 15px;")
        ly = QVBoxLayout(frame)
        
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #7f8c8d; font-size: 14px; font-weight: bold;")
        
        lbl_val = QLabel(valor_inicial)
        lbl_val.setStyleSheet("color: #2c3e50; font-size: 28px; font-weight: bold;")
        
        ly.addWidget(lbl_tit)
        ly.addWidget(lbl_val)
        
        return {"frame": frame, "label_valor": lbl_val}

    def cargar_totales(self):
        """Suma las ventas pero SOLO desde la hora que se abrió la caja hoy"""
        self.input_fisico.clear() 
        
        try:
            # Sumamos asegurándonos que la venta ocurrió DESPUÉS de abrir la caja
            query = """
                SELECT c.metodo_pago, SUM(v.total)
                FROM cobro_venta c
                JOIN orden_venta v ON c.id_venta = v.id_venta
                WHERE c.id_cajero = %s AND c.fecha_cobro >= %s
                GROUP BY c.metodo_pago
            """
            resultados = self.db.fetch_all(query, (self.user_data['id'], self.fecha_apertura))
            
            totales = {"Efectivo": 0.0, "Tarjeta": 0.0, "Transferencia": 0.0}
            
            for fila in (resultados or []):
                metodo, suma = fila[0], fila[1]
                if "Efectivo" in metodo: totales["Efectivo"] += float(suma)
                elif "Tarjeta" in metodo: totales["Tarjeta"] += float(suma)
                elif "Transferencia" in metodo: totales["Transferencia"] += float(suma)

            self.total_efectivo_sistema = totales["Efectivo"]
            self.total_tarjeta = totales["Tarjeta"]
            self.total_transferencia = totales["Transferencia"]

            self.card_efectivo['label_valor'].setText(f"${self.total_efectivo_sistema:,.2f}")
            self.card_tarjeta['label_valor'].setText(f"${self.total_tarjeta:,.2f}")
            self.card_transferencia['label_valor'].setText(f"${self.total_transferencia:,.2f}")

            esperado = self.total_efectivo_sistema + self.fondo_caja
            self.lbl_esperado.setText(f"${esperado:,.2f}  (Fondo: ${self.fondo_caja} + Ventas: ${self.total_efectivo_sistema})")

        except Exception as e:
            AlertaCustom.show_error(self, "Error de Consulta", str(e))

    def calcular_diferencia(self):
        """Verifica en tiempo real si falta o sobra dinero"""
        try:
            texto = self.input_fisico.text().replace(',', '')
            if not texto:
                self.lbl_diferencia.setText("$0.00")
                self.lbl_diferencia.setStyleSheet("font-size: 24px; font-weight: bold; color: #7f8c8d;")
                return

            fisico = float(texto)
            esperado = self.total_efectivo_sistema + self.fondo_caja
            diferencia = fisico - esperado

            if diferencia == 0:
                self.lbl_diferencia.setText("$0.00 (Cuadrado)")
                self.lbl_diferencia.setStyleSheet("font-size: 24px; font-weight: bold; color: #27ae60;")
            elif diferencia > 0:
                self.lbl_diferencia.setText(f"+${diferencia:,.2f} (Sobrante)")
                self.lbl_diferencia.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
            else:
                self.lbl_diferencia.setText(f"-${abs(diferencia):,.2f} (Faltante)")
                self.lbl_diferencia.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c;")
        except ValueError:
            self.lbl_diferencia.setText("Monto inválido")
            self.lbl_diferencia.setStyleSheet("font-size: 24px; font-weight: bold; color: #7f8c8d;")

    def cerrar_turno(self):
        """EL GRAN FINAL: Guarda el corte de caja en PostgreSQL"""
        texto_fisico = self.input_fisico.text().replace(',', '')
        if not texto_fisico:
            AlertaCustom.show_warning(self, "Atención", "Debes ingresar el efectivo físico contado.")
            return

        fisico = float(texto_fisico)
        esperado = self.total_efectivo_sistema + self.fondo_caja
        diferencia = fisico - esperado

        if AlertaCustom.ask_confirm(self, "Cerrar Turno", "¿Estás seguro de emitir el corte? Se cerrará tu sesión automáticamente."):
            try:
                # UPDATE EXACTO A TU TABLA DE CORTES_CAJA
                query_cierre = """
                    UPDATE cortes_caja
                    SET fecha_hora_cierre = CURRENT_TIMESTAMP,
                        efectivo_fisico = %s,
                        total_sistema = %s,
                        diferencia = %s,
                        estatus = 'Cerrada'
                    WHERE id_corte = %s
                """
                self.db.execute_query(query_cierre, (fisico, esperado, diferencia, self.id_corte))
                
                AlertaCustom.show_success(self, "Corte Exitoso", "El turno ha sido cerrado y guardado en auditoría.")
                
                # Cerramos la aplicación o devolvemos a la pantalla de login
                from PyQt6.QtWidgets import QApplication
                QApplication.quit()
                
            except Exception as e:
                AlertaCustom.show_error(self, "Error de Base de Datos", f"Fallo al guardar el corte: {e}")