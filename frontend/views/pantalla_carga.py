# frontend/views/loading_screen.py
import time
import qtawesome as qta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame, QApplication, QGraphicsDropShadowEffect
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
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("LoadingScreen")
        
        # Tamaño responsive
        screen = QApplication.primaryScreen().availableGeometry()
        ancho = int(screen.width() * 0.25)
        alto = int(screen.height() * 0.35)
        
        # Límites razonables ajustados para dar respiro al contenido y la sombra
        ancho = max(450, min(ancho, 600))
        
        # Fijamos solo el ancho y un mínimo de alto para evitar que se achocque
        self.setFixedWidth(ancho)
        self.setMinimumHeight(350)
        
        # Layout principal de la ventana para alojar el contenedor con sombra
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Contenedor principal estilo tarjeta blanca
        contenedor = QFrame()
        contenedor.setObjectName("contenedorCarga")
        contenedor.setStyleSheet("""
            QFrame#contenedorCarga {
                background-color: #ffffff;
                border-radius: 20px;
            }
        """)
        
        # Sombra moderna tipo web
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 10)
        # Bajar opacidad a la sombra para que se vea premium
        color = shadow.color()
        color.setAlpha(40)
        shadow.setColor(color)
        
        contenedor.setGraphicsEffect(shadow)
        main_layout.addWidget(contenedor)
        
        # Layout interno del contenedor
        layout = QVBoxLayout(contenedor)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Icono principal usando qtawesome
        icono_label = QLabel()
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            icono_label.setPixmap(qta.icon('fa5s.store', color='#3b82f6').pixmap(64, 64))
        except Exception:
            icono_label.setText("🔧")
            icono_label.setStyleSheet("font-size: 64px;")
        layout.addWidget(icono_label)
        
        # Logo
        self.logo_label = QLabel("EL TORNILLO FELIZ")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("""
            font-size: 18pt; 
            font-weight: 800; 
            color: #1e293b;
            letter-spacing: 1px;
            font-family: 'Segoe UI', system-ui, sans-serif;
        """)
        layout.addWidget(self.logo_label)

        layout.addSpacing(5)

        # Estado
        self.status_label = QLabel("Verificando conexión con la base de datos...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            font-size: 11pt; 
            color: #64748b;
            font-family: 'Segoe UI', system-ui, sans-serif;
        """)
        layout.addWidget(self.status_label)

        layout.addSpacing(15)

        # Barra de progreso delgada y elegante
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("barraProgresoUnica")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False) 
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar#barraProgresoUnica {
                border: none;
                border-radius: 4px;
                background-color: #e2e8f0;
            }
            QProgressBar#barraProgresoUnica::chunk {
                background-color: #3b82f6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Porcentaje
        self.porcentaje_label = QLabel("0%")
        self.porcentaje_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.porcentaje_label.setStyleSheet("""
            font-size: 11pt; 
            font-weight: 700;
            color: #3b82f6;
            font-family: 'Segoe UI', system-ui, sans-serif;
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
            self.status_label.setStyleSheet("""
                font-size: 11pt; 
                color: #10b981;
                font-family: 'Segoe UI', system-ui, sans-serif;
            """)
            self.porcentaje_label.setText("✓ Completado")
            self.porcentaje_label.setStyleSheet("""
                font-size: 11pt; 
                font-weight: 700;
                color: #10b981;
                font-family: 'Segoe UI', system-ui, sans-serif;
            """)
            self.progress_bar.setStyleSheet("""
                QProgressBar#barraProgresoUnica {
                    border: none;
                    border-radius: 4px;
                    background-color: #e2e8f0;
                }
                QProgressBar#barraProgresoUnica::chunk {
                    background-color: #10b981;
                    border-radius: 4px;
                }
            """)
            QThread.msleep(300)
            self.connection_ready.emit(self.user_data)
        else:
            self.status_label.setText("Error crítico: No se pudo conectar a la base de datos local.")
            self.status_label.setStyleSheet("""
                font-size: 11pt; 
                color: #ef4444; 
                font-family: 'Segoe UI', system-ui, sans-serif;
            """)
            self.porcentaje_label.setText("✗ Error")
            self.porcentaje_label.setStyleSheet("""
                font-size: 11pt; 
                font-weight: 700;
                color: #ef4444;
                font-family: 'Segoe UI', system-ui, sans-serif;
            """)
            self.progress_bar.setStyleSheet("""
                QProgressBar#barraProgresoUnica {
                    border: none;
                    border-radius: 4px;
                    background-color: #e2e8f0;
                }
                QProgressBar#barraProgresoUnica::chunk {
                    background-color: #ef4444;
                    border-radius: 4px;
                }
            """)