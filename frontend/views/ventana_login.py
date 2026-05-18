import qtawesome as qta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QMessageBox, 
                             QFrame, QApplication, QGraphicsDropShadowEffect, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QScreen, QColor, QIcon
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
        self.setObjectName("LoginWindow")
        
        screen = QApplication.primaryScreen().availableGeometry()
        
        ancho = max(450, int(screen.width() * 0.35))
        ancho = min(ancho, 600)
        
        alto = max(600, int(screen.height() * 0.70))
        alto = min(alto, 750)
        
        self.setFixedSize(ancho, alto)
        
        self.setStyleSheet("""
            QWidget#LoginWindow {
                background-color: #e4ebf5;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        contenedor = QFrame()
        card_width = int(ancho * 0.88)
        card_height = int(alto * 0.88)
        contenedor.setFixedSize(card_width, card_height)
        
        contenedor.setStyleSheet("""
            QFrame#LoginCard {
                background-color: #ffffff;
                border-radius: 20px;
            }
        """)
        contenedor.setObjectName("LoginCard")
        main_layout.addWidget(contenedor)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 10)
        contenedor.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(contenedor)
        layout.setSpacing(int(alto * 0.03))
        
        margen_h = int(card_width * 0.12)
        margen_v = int(card_height * 0.10)
        layout.setContentsMargins(margen_h, margen_v, margen_h, margen_v)
        
        icono_superior = QLabel()
        icono_superior.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            icono_superior.setPixmap(qta.icon('fa5s.store', color='#2563eb').pixmap(60, 60))
        except Exception:
            pass
        layout.addWidget(icono_superior)
        
        titulo_principal = QLabel("FERRETERÍA")
        titulo_principal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        titulo_principal.setStyleSheet("""
            font-size: 24pt; 
            font-weight: 800; 
            color: #1e293b;
            letter-spacing: 1px;
            margin-top: 5px;
            font-family: 'Segoe UI', system-ui, sans-serif;
        """)
        layout.addWidget(titulo_principal)
        
        self.title_label = QLabel("Ingresa a tu cuenta")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 11pt; 
            color: #64748b;
            margin-bottom: 25px;
            font-family: 'Segoe UI', system-ui, sans-serif;
        """)
        layout.addWidget(self.title_label)

        altura_input = int(alto * 0.075)

        user_group = QVBoxLayout()
        user_group.setSpacing(6)
        
        label_usuario = QLabel("USUARIO")
        label_usuario.setStyleSheet("""
            font-size: 10pt; 
            font-weight: 700; 
            color: #64748b;
            font-family: 'Segoe UI', system-ui, sans-serif;
        """)
        user_group.addWidget(label_usuario)
        
        self.user_input = FormInput("Ej. admin")
        try:
            icon_user = qta.icon('fa5s.user', color='#94a3b8')
            self.user_input.addAction(icon_user, QLineEdit.ActionPosition.LeadingPosition)
        except Exception:
            pass
            
        self.user_input.setMinimumHeight(altura_input)
        self.user_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 5px 15px;
                font-size: 12pt;
                background-color: #f8fafc;
                color: #0f172a;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background-color: #ffffff;
            }
        """)
        user_group.addWidget(self.user_input)
        layout.addLayout(user_group)

        layout.addSpacing(int(alto * 0.02))

        pin_group = QVBoxLayout()
        pin_group.setSpacing(6)
        
        label_pin = QLabel("PIN DE SEGURIDAD")
        label_pin.setStyleSheet("""
            font-size: 10pt; 
            font-weight: 700; 
            color: #64748b;
            font-family: 'Segoe UI', system-ui, sans-serif;
        """)
        pin_group.addWidget(label_pin)
        
        self.pin_input = FormInput("****")
        self.pin_input.setEchoMode(FormInput.EchoMode.Password)
        self.pin_input.setMaxLength(4)
        
        try:
            icon_lock = qta.icon('fa5s.lock', color='#94a3b8')
            self.pin_input.addAction(icon_lock, QLineEdit.ActionPosition.LeadingPosition)
        except Exception:
            pass
            
        self.pin_input.setMinimumHeight(altura_input)
        self.pin_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 5px 15px;
                font-size: 12pt;
                background-color: #f8fafc;
                color: #0f172a;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background-color: #ffffff;
            }
        """)
        pin_group.addWidget(self.pin_input)
        layout.addLayout(pin_group)

        layout.addSpacing(int(alto * 0.04))

        self.login_btn = PrimaryButton("  Ingresar al Sistema")
        try:
            self.login_btn.setIcon(qta.icon('fa5s.arrow-right', color='white'))
        except Exception:
            pass
            
        altura_boton = int(alto * 0.08)
        self.login_btn.setMinimumHeight(altura_boton)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12pt;
                font-weight: 700;
                padding: 10px;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        layout.addStretch()
        
        footer = QLabel("Sistema de Gestión v1.0")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("""
            color: #94a3b8;
            font-size: 9pt;
            margin-top: 10px;
            font-family: 'Segoe UI', system-ui, sans-serif;
        """)
        layout.addWidget(footer)

    def centrar_ventana(self):
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