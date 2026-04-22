# frontend/views/loading_screen.py
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QApplication
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from backend.bd_conexion import DatabaseConnection

class ConnectionWorker(QThread):
    finished = pyqtSignal(bool)
    progress = pyqtSignal(int)

    def run(self):
        # Simulamos la verificación técnica
        for i in range(1, 101):
            time.sleep(0.015)
            self.progress.emit(i)
            
        # Intentamos conectar realmente a la BD
        db = DatabaseConnection()
        success = db.connection is not None
        self.finished.emit(success)


class LoadingScreen(QWidget):
    connection_ready = pyqtSignal(dict)

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.init_ui()
        self.centrar_ventana()
        
        # Iniciar el worker después de inicializar la UI
        self.iniciar_worker()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("LoadingScreen")
        
        # Tamaño responsive
        screen = QApplication.primaryScreen().availableGeometry()
        ancho = int(screen.width() * 0.25)
        alto = int(screen.height() * 0.35)
        
        # Límites razonables
        ancho = max(400, min(ancho, 550))
        alto = max(280, min(alto, 380))
        
        self.setFixedSize(ancho, alto)
        
        # Estilo específico para esta pantalla (sin afectar al tema global)
        self.setStyleSheet("""
            #LoadingScreen {
                background-color: #f8f9fa;
            }
        """)
        
        # Contenedor principal
        contenedor = QFrame(self)
        contenedor.setGeometry(0, 0, ancho, alto)
        contenedor.setObjectName("contenedorCarga")
        contenedor.setStyleSheet("""
            #contenedorCarga {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #dee2e6;
            }
        """)
        
        # Layout
        margen = int(ancho * 0.08)
        layout = QVBoxLayout(contenedor)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(int(alto * 0.05))
        layout.setContentsMargins(margen, margen, margen, margen)
        
        # Icono
        icono_label = QLabel("🔧")
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_size_icono = int(ancho * 0.1)
        icono_label.setStyleSheet(f"""
            font-size: {font_size_icono}px;
            background-color: transparent;
        """)
        layout.addWidget(icono_label)
        
        # Logo
        self.logo_label = QLabel("EL TORNILLO FELIZ")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_size_logo = int(ancho * 0.06)
        self.logo_label.setStyleSheet(f"""
            font-size: {font_size_logo}px; 
            font-weight: bold; 
            color: #2c3e50;
            letter-spacing: 1px;
            background-color: transparent;
        """)
        layout.addWidget(self.logo_label)

        # Estado
        self.status_label = QLabel("Verificando conexión con la base de datos...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        font_size_status = int(ancho * 0.032)
        self.status_label.setStyleSheet(f"""
            font-size: {font_size_status}px; 
            color: #6c757d;
            background-color: transparent;
            padding: 5px;
        """)
        layout.addWidget(self.status_label)

        # Barra de progreso - IMPORTANTE: Usar un nombre de objeto único
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("barraProgresoUnica")
        self.progress_bar.setValue(0)
        altura_barra = int(alto * 0.06)
        self.progress_bar.setFixedHeight(altura_barra)
        self.progress_bar.setStyleSheet("""
            QProgressBar#barraProgresoUnica {
                border: 1px solid #ced4da;
                border-radius: 6px;
                text-align: center;
                background-color: #f1f3f5;
            }
            QProgressBar#barraProgresoUnica::chunk {
                background-color: #3498db;
                border-radius: 5px;
                margin: 1px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Porcentaje
        self.porcentaje_label = QLabel("0%")
        self.porcentaje_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_size_porcentaje = int(ancho * 0.035)
        self.porcentaje_label.setStyleSheet(f"""
            font-size: {font_size_porcentaje}px; 
            font-weight: bold;
            color: #495057;
            background-color: transparent;
        """)
        layout.addWidget(self.porcentaje_label)
        
        layout.addStretch()

    def iniciar_worker(self):
        """Inicia el worker en un hilo separado"""
        self.worker = ConnectionWorker()
        self.worker.progress.connect(self.actualizar_progreso)
        self.worker.finished.connect(self.on_verification_finished)
        self.worker.start()

    def actualizar_progreso(self, valor):
        """Actualiza tanto la barra como el texto de porcentaje"""
        self.progress_bar.setValue(valor)
        self.porcentaje_label.setText(f"{valor}%")

    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def on_verification_finished(self, success):
        if success:
            self.status_label.setText("¡Conexión exitosa! Cargando sistema...")
            self.status_label.setStyleSheet(f"""
                font-size: {int(self.width() * 0.032)}px; 
                color: #28a745; 
                font-weight: 600;
                background-color: transparent;
            """)
            self.porcentaje_label.setText("✓ Completado")
            self.porcentaje_label.setStyleSheet(f"""
                font-size: {int(self.width() * 0.035)}px; 
                font-weight: bold;
                color: #28a745;
                background-color: transparent;
            """)
            QThread.msleep(300)
            self.connection_ready.emit(self.user_data)
        else:
            self.status_label.setText("Error crítico: No se pudo conectar a la base de datos local.")
            self.status_label.setStyleSheet(f"""
                font-size: {int(self.width() * 0.032)}px; 
                color: #dc3545; 
                font-weight: 600;
                background-color: transparent;
            """)
            self.porcentaje_label.setText("✗ Error")
            self.porcentaje_label.setStyleSheet(f"""
                font-size: {int(self.width() * 0.035)}px; 
                font-weight: bold;
                color: #dc3545;
                background-color: transparent;
            """)
            self.progress_bar.setStyleSheet("""
                QProgressBar#barraProgresoUnica {
                    border: 1px solid #ced4da;
                    border-radius: 6px;
                    text-align: center;
                    background-color: #f1f3f5;
                }
                QProgressBar#barraProgresoUnica::chunk {
                    background-color: #dc3545;
                    border-radius: 5px;
                    margin: 1px;
                }
            """)