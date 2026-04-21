# frontend/views/login_window.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from backend.servicio_auth import AuthService
from frontend.components.elementos_ui import FormInput, PrimaryButton

class LoginWindow(QWidget):
    # ¡AQUÍ ESTÁ LA CLAVE! La señal se define a nivel de clase
    login_success = pyqtSignal(dict) 

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Ferretería - Acceso al Sistema")
        self.setFixedSize(350, 450)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Encabezado
        self.title_label = QLabel("BIENVENIDO")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.title_label)

        # Campo Usuario (Usando el componente reutilizable)
        layout.addWidget(QLabel("Nombre de Usuario:"))
        self.user_input = FormInput("Ej: admin")
        layout.addWidget(self.user_input)

        # Campo PIN (Usando el componente reutilizable)
        layout.addWidget(QLabel("PIN de 4 dígitos:"))
        self.pin_input = FormInput("****")
        self.pin_input.setEchoMode(FormInput.EchoMode.Password)
        self.pin_input.setMaxLength(4)
        layout.addWidget(self.pin_input)

        # Botón de Inicio (Usando el componente reutilizable)
        self.login_btn = PrimaryButton("Iniciar Sesión")
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def handle_login(self):
        user = self.user_input.text()
        pin = self.pin_input.text()

        if not user or not pin:
            QMessageBox.warning(self, "Campos vacíos", "Por favor completa todos los campos.")
            return

        # Verificamos contra la base de datos
        session = self.auth_service.login(user, pin)

        if session:
            # Emitimos la señal enviando el diccionario con los datos del usuario
            self.login_success.emit(session)
        else:
            QMessageBox.critical(self, "Error de Acceso", "Usuario o PIN incorrectos, o cuenta inactiva.")