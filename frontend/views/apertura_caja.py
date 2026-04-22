# frontend/views/apertura_caja.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from frontend.components.elementos_ui import PrimaryButton
from frontend.components.alertas import AlertaCustom
from backend.bd_conexion import DatabaseConnection

class AperturaCajaModal(QDialog):
    def __init__(self, id_cajero, parent=None):
        super().__init__(parent)
        self.id_cajero = id_cajero
        self.db = DatabaseConnection()
        self.id_corte_generado = None
        self.fondo_ingresado = 0.0
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Apertura de Caja")
        self.setFixedSize(350, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("background-color: white; border: 2px solid #2c3e50; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_titulo = QLabel("<b>APERTURA DE TURNO</b>")
        lbl_titulo.setStyleSheet("font-size: 18px; color: #3498db;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        layout.addWidget(QLabel("Ingresa el fondo inicial (Efectivo base en cajón):"))
        
        self.input_fondo = QLineEdit()
        self.input_fondo.setPlaceholderText("Ej. 500.00")
        self.input_fondo.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px; border: 1px solid #bdc3c7;")
        layout.addWidget(self.input_fondo)

        layout.addStretch()

        self.btn_abrir = PrimaryButton("ABRIR CAJA")
        self.btn_abrir.setStyleSheet("background-color: #27ae60; font-size: 14px; padding: 10px;")
        self.btn_abrir.clicked.connect(self.registrar_apertura)
        layout.addWidget(self.btn_abrir)

    def registrar_apertura(self):
        texto = self.input_fondo.text().strip()
        if not texto:
            AlertaCustom.show_warning(self, "Atención", "Debes ingresar un monto.")
            return
            
        try:
            self.fondo_ingresado = float(texto)
            # Insertamos en tu tabla cortes_caja
            query = """
                INSERT INTO cortes_caja (id_cajero, fecha_hora_apertura, fondo_inicial, estatus)
                VALUES (%s, CURRENT_TIMESTAMP, %s, 'Abierta') RETURNING id_corte
            """
            res = self.db.fetch_one(query, (self.id_cajero, self.fondo_ingresado))
            self.id_corte_generado = res[0]
            self.accept()
        except ValueError:
            AlertaCustom.show_error(self, "Error", "Monto inválido. Ingresa solo números.")
        except Exception as e:
            AlertaCustom.show_error(self, "Error de BD", f"No se pudo abrir caja: {e}")