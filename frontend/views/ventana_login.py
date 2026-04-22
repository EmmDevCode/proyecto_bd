# frontend/views/login_window.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QMessageBox, QFrame, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QScreen
from backend.servicio_auth import AuthService
from frontend.components.elementos_ui import FormInput, PrimaryButton

class LoginWindow(QWidget):
    login_success = pyqtSignal(dict) 

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.init_ui()
        self.centrar_ventana()

    def init_ui(self):
        self.setWindowTitle("Ferresoft - Acceso al Sistema")
        
        # Tamaño responsive basado en la pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        ancho = int(screen.width() * 0.28)  # 28% del ancho de pantalla
        alto = int(screen.height() * 0.55)   # 55% del alto de pantalla
        
        # Límites para que no sea ni muy pequeño ni muy grande
        ancho = max(380, min(ancho, 500))
        alto = max(480, min(alto, 600))
        
        self.setFixedSize(ancho, alto)
        self.setStyleSheet("background-color: #f4f6f9;")
        
        # Contenedor principal
        contenedor = QFrame(self)
        contenedor.setGeometry(0, 0, ancho, alto)
        contenedor.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dcdde1;
            }
        """)
        
        # Layout con márgenes proporcionales
        margen_h = int(ancho * 0.12)  # 12% de margen horizontal
        margen_v = int(alto * 0.1)     # 10% de margen vertical
        
        layout = QVBoxLayout(contenedor)
        layout.setSpacing(int(alto * 0.03))
        layout.setContentsMargins(margen_h, margen_v, margen_h, margen_v)
        
        # Logo / Título
        titulo_principal = QLabel("FERRETERÍA")
        titulo_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Tamaño de fuente responsive
        font_size_titulo = int(ancho * 0.07)
        titulo_principal.setStyleSheet(f"""
            font-size: {font_size_titulo}px; 
            font-weight: bold; 
            color: #2c3e50;
            letter-spacing: 2px;
            margin-bottom: 10px;
        """)
        layout.addWidget(titulo_principal)
        
        # Línea separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #ecf0f1; max-height: 2px;")
        layout.addWidget(separador)

        # Subtítulo
        self.title_label = QLabel("Inicio de Sesión")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_size_subtitulo = int(ancho * 0.045)
        self.title_label.setStyleSheet(f"""
            font-size: {font_size_subtitulo}px; 
            font-weight: 600; 
            color: #34495e;
            margin: 10px 0px;
        """)
        layout.addWidget(self.title_label)

        # Campo Usuario
        font_size_label = int(ancho * 0.032)
        label_usuario = QLabel("Usuario:")
        label_usuario.setStyleSheet(f"""
            font-size: {font_size_label}px; 
            font-weight: bold; 
            color: #576574;
            margin-bottom: -15px;
        """)
        layout.addWidget(label_usuario)
        
        self.user_input = FormInput("Usuario")
        altura_input = int(alto * 0.07)
        self.user_input.setMinimumHeight(altura_input)
        font_size_input = int(ancho * 0.035)
        self.user_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid #dcdde1;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: {font_size_input}px;
                background-color: white;
                color: #2f3640;
            }}
            QLineEdit:focus {{
                border: 1.5px solid #3498db;
                background-color: #f8f9fa;
            }}
        """)
        layout.addWidget(self.user_input)

        # Campo PIN
        label_pin = QLabel("PIN (4 dígitos):")
        label_pin.setStyleSheet(f"""
            font-size: {font_size_label}px; 
            font-weight: bold; 
            color: #576574;
            margin-bottom: -15px;
        """)
        layout.addWidget(label_pin)
        
        self.pin_input = FormInput("****")
        self.pin_input.setEchoMode(FormInput.EchoMode.Password)
        self.pin_input.setMaxLength(4)
        self.pin_input.setMinimumHeight(altura_input)
        self.pin_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid #dcdde1;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: {font_size_input}px;
                background-color: white;
                color: #2f3640;
            }}
            QLineEdit:focus {{
                border: 1.5px solid #3498db;
                background-color: #f8f9fa;
            }}
        """)
        layout.addWidget(self.pin_input)

        layout.addSpacing(int(alto * 0.03))

        # Botón de Inicio
        self.login_btn = PrimaryButton("Ingresar al Sistema")
        altura_boton = int(alto * 0.075)
        self.login_btn.setMinimumHeight(altura_boton)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        font_size_boton = int(ancho * 0.035)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: {font_size_boton}px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:pressed {{
                background-color: #2471a3;
            }}
        """)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        layout.addStretch()
        
        # Footer
        footer = QLabel("Sistema de Gestión")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_size_footer = int(ancho * 0.028)
        footer.setStyleSheet(f"""
            color: #95a5a6;
            font-size: {font_size_footer}px;
            margin-top: 15px;
        """)
        layout.addWidget(footer)

    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def handle_login(self):
        user = self.user_input.text()
        pin = self.pin_input.text()

        if not user or not pin:
            QMessageBox.warning(self, "Campos vacíos", "Por favor completa todos los campos.")
            return

        session = self.auth_service.login(user, pin)

        if session:
            self.login_success.emit(session)
        else:
            QMessageBox.critical(self, "Error de Acceso", "Usuario o PIN incorrectos, o cuenta inactiva.")