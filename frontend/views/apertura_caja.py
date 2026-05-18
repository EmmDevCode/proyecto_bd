# frontend/views/apertura_caja.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
import qtawesome as qta

from backend.bd_conexion import DatabaseConnection
from frontend.components.elementos_ui import BotonConfirmar
from frontend.components.alertas import AlertaCustom

class AperturaCajaModal(QDialog):
    """Ventanita obligatoria para que el cajero declare el efectivo al iniciar su turno"""
    def __init__(self, id_cajero, parent=None):
        super().__init__(parent)
        self.id_cajero = id_cajero
        self.db = DatabaseConnection()
        self.id_corte_generado = None
        self.fondo_ingresado = 0.0
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Apertura de Turno - Arqueo Inicial")
        self.setFixedSize(400, 360)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # --- TÍTULO E INSTRUCCIONES ---
        lbl_titulo = QLabel("Arqueo Inicial de Efectivo")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        lbl_instrucciones = QLabel("Ingresa el monto exacto con el que abres el cajón de dinero. Las terminales inician en $0.00.")
        lbl_instrucciones.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        lbl_instrucciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_instrucciones.setWordWrap(True)
        layout.addWidget(lbl_instrucciones)

        # --- FORMULARIO DE EFECTIVO ---
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)

        # Validador para aceptar solo formato de dinero (ej. 1500.50)
        validador = QDoubleValidator(0.00, 999999.99, 2)
        validador.setNotation(QDoubleValidator.Notation.StandardNotation)

        # 1. Input de Billetes
        self.input_billetes = QLineEdit()
        self.input_billetes.setPlaceholderText("0.00")
        self.input_billetes.setValidator(validador)
        self.input_billetes.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self.input_billetes.addAction(qta.icon('fa5s.money-bill-wave', color='#27ae60'), QLineEdit.ActionPosition.LeadingPosition)
        self.input_billetes.textChanged.connect(self.actualizar_total)
        form_layout.addRow(QLabel("<b>Billetes ($):</b>"), self.input_billetes)

        # 2. Input de Monedas
        self.input_monedas = QLineEdit()
        self.input_monedas.setPlaceholderText("0.00")
        self.input_monedas.setValidator(validador)
        self.input_monedas.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self.input_monedas.addAction(qta.icon('fa5s.coins', color='#f39c12'), QLineEdit.ActionPosition.LeadingPosition)
        self.input_monedas.textChanged.connect(self.actualizar_total)
        form_layout.addRow(QLabel("<b>Monedas ($):</b>"), self.input_monedas)

        layout.addLayout(form_layout)

    
        self.lbl_total = QLabel("Total en Caja: $ 0.00")
        self.lbl_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #2980b9; margin-top: 10px;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_total)

        layout.addStretch()

      
        self.btn_abrir = BotonConfirmar("ABRIR TURNO")
        self.btn_abrir.clicked.connect(self.abrir_turno)
        layout.addWidget(self.btn_abrir)

    def actualizar_total(self):
        """Calcula la suma en tiempo real mientras el cajero teclea"""
        try:
            billetes = float(self.input_billetes.text() or 0)
            monedas = float(self.input_monedas.text() or 0)
            total = billetes + monedas
            self.lbl_total.setText(f"Total en Caja: $ {total:,.2f}")
        except ValueError:
            self.lbl_total.setText("Total en Caja: $ 0.00")

    def abrir_turno(self):
        """Manda los datos limpios y desglosados a PostgreSQL"""
        try:
            billetes = float(self.input_billetes.text() or 0)
            monedas = float(self.input_monedas.text() or 0)
            total_fondo = billetes + monedas
        except ValueError:
            AlertaCustom.show_error(self, "Error", "Por favor ingresa cantidades numéricas válidas.")
            return

        if total_fondo < 0:
            AlertaCustom.show_error(self, "Error", "El fondo inicial no puede ser negativo.")
            return


        query = """
            INSERT INTO cortes_caja (id_cajero, fecha_hora_apertura, fondo_inicial, fondo_billetes, fondo_monedas, estatus)
            VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, 'Abierta')
            RETURNING id_corte
        """
        
        try:
        
            res = self.db.fetch_one(query, (self.id_cajero, total_fondo, billetes, monedas))
            if res:
                self.id_corte_generado = res[0]
                self.fondo_ingresado = total_fondo
                self.accept() # Cierra la ventana modal con éxito
            else:
                AlertaCustom.show_error(self, "Error", "No se pudo registrar la apertura en la base de datos.")
        except Exception as e:
             AlertaCustom.show_error(self, "Error BD", f"Hubo un problema de conexión: {str(e)}")