# frontend/components/alertas.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QIcon, QPainter, QBrush, QColor, QPen

class AlertaCustom(QDialog):
    def __init__(self, parent, titulo, mensaje, tipo="info"):
        super().__init__(parent)
        self.respuesta_confirmacion = False
        self.init_ui(titulo, mensaje, tipo)
        self.aplicar_animacion_entrada()

    def init_ui(self, titulo, mensaje, tipo):
        self.setWindowTitle(titulo)
        self.setFixedSize(480, 260)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Paleta de colores modernizada
        colores = {
            "success": {
                "principal": "#10b981",    # Emerald
                "secundario": "#059669",
                "fondo": "#ecfdf5",
                "borde": "#a7f3d0",
                "icono": "✓"
            },
            "info": {
                "principal": "#3b82f6",    # Blue
                "secundario": "#2563eb", 
                "fondo": "#eff6ff",
                "borde": "#bfdbfe",
                "icono": "ℹ"
            },
            "warning": {
                "principal": "#f59e0b",    # Amber
                "secundario": "#d97706",
                "fondo": "#fffbeb",
                "borde": "#fde68a",
                "icono": "⚠"
            },
            "error": {
                "principal": "#ef4444",    # Red
                "secundario": "#dc2626",
                "fondo": "#fef2f2",
                "borde": "#fecaca",
                "icono": "✕"
            },
            "confirm": {
                "principal": "#6366f1",    # Indigo
                "secundario": "#4f46e5",
                "fondo": "#eef2ff",
                "borde": "#c7d2fe",
                "icono": "?"
            }
        }
        
        tema = colores.get(tipo, colores["info"])
        
        # Contenedor principal con fondo (Estilo Flat moderno)
        contenedor = QFrame(self)
        contenedor.setObjectName("contenedorAlerta")
        contenedor.setStyleSheet(f"""
            #contenedorAlerta {{
                background-color: #ffffff;
                border: 2px solid {tema['borde']};
                border-radius: 16px;
            }}
        """)
        # Agregar sombra suave al contenedor
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        contenedor.setGraphicsEffect(shadow)
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(2, 2, 2, 2)
        layout_principal.addWidget(contenedor)
        
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        # Cabecera con icono y título
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Círculo con icono (Fondo suave)
        circulo_icono = QLabel(tema['icono'])
        circulo_icono.setFixedSize(48, 48)
        circulo_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circulo_icono.setStyleSheet(f"""
            QLabel {{
                background-color: {tema['fondo']};
                color: {tema['principal']};
                border-radius: 24px;
                font-size: 24px;
                font-weight: bold;
                border: 2px solid {tema['borde']};
            }}
        """)
        header_layout.addWidget(circulo_icono)
        
        # Título
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 700;
                color: {tema['secundario']};
                letter-spacing: -0.3px;
            }}
        """)
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        
        # Botón cerrar (X)
        btn_cerrar = QPushButton("×")
        btn_cerrar.setFixedSize(32, 32)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: none;
                border-radius: 8px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                color: #4b5563;
            }
        """)
        btn_cerrar.clicked.connect(self.reject)
        header_layout.addWidget(btn_cerrar)
        
        layout.addLayout(header_layout)

        # Línea separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet(f"""
            background-color: {tema['borde']};
            max-height: 1px;
        """)
        layout.addWidget(separador)

        # Cuerpo del Mensaje
        lbl_mensaje = QLabel(mensaje)
        lbl_mensaje.setWordWrap(True)
        lbl_mensaje.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lbl_mensaje.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #4b5563;
                line-height: 1.6;
                padding: 5px 0px;
            }
        """)
        layout.addWidget(lbl_mensaje)
        
        layout.addStretch()

        # Botonera
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(12)

        if tipo == "confirm":
            btn_no = self.crear_boton_moderno("Cancelar", "#9ca3af", es_primario=False)
            btn_no.clicked.connect(self.reject)
            
            btn_si = self.crear_boton_moderno("Confirmar", tema['principal'], es_primario=True)
            btn_si.clicked.connect(self.aceptar_confirmacion)
            
            botones_layout.addStretch()
            botones_layout.addWidget(btn_no)
            botones_layout.addWidget(btn_si)
        else:
            texto_boton = {
                "success": "¡Entendido!",
                "error": "Aceptar",
                "warning": "Entendido",
                "info": "Continuar"
            }.get(tipo, "Aceptar")
            
            btn_ok = self.crear_boton_moderno(texto_boton, tema['principal'], es_primario=True)
            btn_ok.clicked.connect(self.accept)
            botones_layout.addStretch()
            botones_layout.addWidget(btn_ok)
            botones_layout.addStretch()

        layout.addLayout(botones_layout)

    def crear_boton_moderno(self, texto, color, es_primario=True):
        btn = QPushButton(texto)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        
        if es_primario:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border-radius: 8px;
                    padding: 0px 24px;
                    font-weight: 700;
                    font-size: 13px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {self.oscurecer_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {color};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {color};
                    border: 1.5px solid {color};
                    border-radius: 8px;
                    padding: 0px 24px;
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {color}15;
                    border-width: 2px;
                }}
                QPushButton:pressed {{
                    background-color: {color}30;
                }}
            """)
        
        return btn
    
    def oscurecer_color(self, color_hex):
        """Oscurece un color hexadecimal un 15%"""
        color = QColor(color_hex)
        return color.darker(115).name()
    
    def aclarar_color(self, color_hex):
        """Aclara un color hexadecimal un 15%"""
        color = QColor(color_hex)
        return color.lighter(115).name()

    def aplicar_animacion_entrada(self):
        """Aplica una suave animación de entrada"""
        self.animacion = QPropertyAnimation(self, b"windowOpacity")
        self.animacion.setDuration(200)
        self.animacion.setStartValue(0)
        self.animacion.setEndValue(1)
        self.animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animacion.start()

    def aceptar_confirmacion(self):
        self.respuesta_confirmacion = True
        self.accept()

    @staticmethod
    def show_success(parent, titulo, mensaje):
        AlertaCustom(parent, titulo, mensaje, "success").exec()

    @staticmethod
    def show_error(parent, titulo, mensaje):
        AlertaCustom(parent, titulo, mensaje, "error").exec()

    @staticmethod
    def ask_confirm(parent, titulo, mensaje):
        dialog = AlertaCustom(parent, titulo, mensaje, "confirm")
        dialog.exec()
        return dialog.respuesta_confirmacion
    
    @staticmethod
    def show_info(parent, titulo, mensaje):
        AlertaCustom(parent, titulo, mensaje, "info").exec()