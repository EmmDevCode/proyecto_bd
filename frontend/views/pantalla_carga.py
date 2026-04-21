# frontend/views/loading_screen.py
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from backend.bd_conexion import DatabaseConnection

class ConnectionWorker(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(int)

    def run(self):
        # Simulamos la verificación técnica requerida para que se vea la animación
        for i in range(1, 101):
            time.sleep(0.015) # Simulación de carga fluida
            self.progress.emit(i)
            
        # Intentamos conectar realmente a la BD
        db = DatabaseConnection()
        success = db.connection is not None
        self.finished.emit(success)


class LoadingScreen(QWidget):
    # ¡AQUÍ ESTÁ LA SEÑAL CORREGIDA! A nivel de clase
    connection_ready = pyqtSignal(dict)

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) # Sin bordes de ventana
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Logotipo
        self.logo_label = QLabel("🔩 EL TORNILLO FELIZ")
        self.logo_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)

        # Leyenda requerida por tus documentos
        self.status_label = QLabel("Verificando la conexión con la base de datos...")
        self.status_label.setStyleSheet("font-size: 14px; color: #34495e;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Barra de progreso estilizada (Tema Claro)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                text-align: center;
                background-color: #f5f6fa;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        
        # Iniciar el trabajador en un hilo separado
        self.worker = ConnectionWorker()
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_verification_finished)
        self.worker.start()

    def on_verification_finished(self, success):
        if success:
            self.status_label.setText("¡Conexión exitosa! Abriendo módulo...")
            self.status_label.setStyleSheet("font-size: 14px; color: #27ae60; font-weight: bold;")
            # Emitimos la señal con los datos del usuario hacia main.py
            self.connection_ready.emit(self.user_data)
        else:
            self.status_label.setText("Error crítico: No se pudo conectar a la base de datos local.")
            self.status_label.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")