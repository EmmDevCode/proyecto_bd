# frontend/components/sidebar.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QFrame, QScrollArea, QLabel)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve

class MenuColapsable(QWidget):
    """Componente personalizado para un menú con animación de acordeón"""
    def __init__(self, titulo, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.titulo_base = titulo
        
        # Botón toggle
        self.btn_toggle = QPushButton(f"▶  {self.titulo_base}")
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                color: #e2e8f0; 
                text-align: left; 
                padding: 14px 20px;
                font-weight: 600; 
                border: none; 
                font-size: 13px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2d3748, stop:1 #1a202c);
                border-bottom: 1px solid #4a5568;
                letter-spacing: 0.3px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3a4a5e, stop:1 #2d3748);
                color: #f7fafc;
                padding-left: 24px;
            }
        """)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.animar_toggle)
        self.layout.addWidget(self.btn_toggle)

        self.area_contenido = QFrame()
        self.area_contenido.setStyleSheet("""
            background-color: #1a202c;
            border-left: 1px solid #4a5568;
            margin-left: 8px;
        """)
        self.layout_contenido = QVBoxLayout(self.area_contenido)
        self.layout_contenido.setContentsMargins(0, 0, 0, 0)
        self.layout_contenido.setSpacing(1)
        self.layout.addWidget(self.area_contenido)

        self.animacion = QPropertyAnimation(self.area_contenido, b"maximumHeight")
        self.animacion.setDuration(300) 
        self.animacion.setEasingCurve(QEasingCurve.Type.OutCubic) 

        self.expandido = False

    def agregar_boton(self, boton):
        self.layout_contenido.addWidget(boton)

    def inicializar_altura(self):
        self.area_contenido.setMaximumHeight(0)

    def animar_toggle(self):
        altura_maxima = self.layout_contenido.sizeHint().height()
        
        if self.expandido:
            self.animacion.setStartValue(altura_maxima)
            self.animacion.setEndValue(0)
            self.btn_toggle.setText(f"▶  {self.titulo_base}")
            self.expandido = False
        else:
            self.animacion.setStartValue(0)
            self.animacion.setEndValue(altura_maxima)
            self.btn_toggle.setText(f"▼  {self.titulo_base}")
            self.expandido = True
            
        self.animacion.start()


class Sidebar(QFrame):
    def __init__(self, titulo, config_menu, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self.setObjectName("SidebarPrincipal")
        self.setStyleSheet("""
            #SidebarPrincipal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a202c, stop:1 #0f1419);
                border-right: 1px solid #2d3748;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1a202c;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #4a5568;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #718096;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        self.botones_registro = {}
        self.config_menu = config_menu
        self.titulo_actual = titulo
        self.init_ui()

    def init_ui(self):
        # Limpiar layout existente si lo hay
        if self.layout():
            QWidget().setLayout(self.layout())
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # Cabecera Fija
        self.lbl_header = QLabel(self.titulo_actual)
        self.lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_header.setStyleSheet("""
            QLabel {
                color: #f7fafc; 
                font-size: 20px; 
                font-weight: 700;
                padding: 28px 10px; 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1419, stop:1 #1a202c);
                border-bottom: 2px solid #ed8936;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
        """)
        layout_principal.addWidget(self.lbl_header)

        # Área con Scroll
        area_scroll = QScrollArea()
        area_scroll.setWidgetResizable(True)
        area_scroll.setFrameShape(QFrame.Shape.NoFrame)
        area_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.widget_scroll = QWidget()
        self.widget_scroll.setStyleSheet("background: transparent;")
        self.layout_scroll = QVBoxLayout(self.widget_scroll)
        self.layout_scroll.setContentsMargins(0, 0, 0, 0)
        self.layout_scroll.setSpacing(2)
        self.layout_scroll.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Construcción dinámica según el tipo de menú
        self.construir_menu(self.config_menu)
        
        area_scroll.setWidget(self.widget_scroll)
        layout_principal.addWidget(area_scroll)

    def construir_menu(self, config_menu):
        """Reconstruye el menú según la configuración proporcionada"""
        # Limpiar registro de botones
        self.botones_registro.clear()
        
        # Limpiar layout scroll
        while self.layout_scroll.count():
            child = self.layout_scroll.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.limpiar_layout(child.layout())
        
        # Verificar si hay categorías colapsables
        tiene_categorias = any(isinstance(opciones, dict) for opciones in config_menu.values())
        
        for categoria, opciones in config_menu.items():
            if isinstance(opciones, dict):
                # Es un menú con animación
                menu_animado = MenuColapsable(categoria)
                for nombre, funcion in opciones.items():
                    btn = self.crear_boton(nombre, funcion, es_sub=True)
                    menu_animado.agregar_boton(btn)
                    self.botones_registro[nombre] = btn
                menu_animado.inicializar_altura()
                self.layout_scroll.addWidget(menu_animado)
            else:
                # Es un botón directo
                btn = self.crear_boton(categoria, opciones, es_sub=False)
                self.layout_scroll.addWidget(btn)
                self.botones_registro[categoria] = btn
        
        # Solo agregar stretch (el separador ya no es necesario)
        self.layout_scroll.addStretch()

    def limpiar_layout(self, layout):
        """Limpia recursivamente un layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.limpiar_layout(child.layout())

    def crear_boton(self, texto, funcion, es_sub):
        """Crea un botón con el estilo apropiado"""
        if es_sub:
            # Botón de submenú (dentro de categoría colapsable)
            btn = QPushButton(f"  {texto}")
            btn.setStyleSheet("""
                QPushButton {
                    color: #a0aec0; 
                    text-align: left; 
                    padding: 12px 15px 12px 45px;
                    border: none;
                    font-size: 12.5px; 
                    background-color: transparent;
                    border-left: 2px solid transparent;
                }
                QPushButton:hover { 
                    background-color: #2d3748; 
                    color: #f7fafc;
                    border-left: 2px solid #ed8936;
                }
            """)
        else:
            # Botón normal (sin comportamiento de acordeón)
            btn = QPushButton(texto)
            btn.setStyleSheet("""
                QPushButton {
                    color: #e2e8f0; 
                    text-align: left; 
                    padding: 14px 20px;
                    border: none;
                    font-size: 13.5px; 
                    font-weight: 500;
                    background-color: transparent;
                    border-bottom: 1px solid #2d3748;
                    letter-spacing: 0.3px;
                }
                QPushButton:hover { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #2d3748, stop:1 #1a202c);
                    color: #ffffff;
                    padding-left: 24px;
                }
                QPushButton:pressed {
                    background-color: #1a202c;
                    padding-left: 24px;
                }
            """)
        
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if funcion: 
            btn.clicked.connect(funcion)
        return btn

    def resaltar_boton(self, nombre_activo):
        """Cambia el estilo del botón seleccionado"""
        for nombre, btn in self.botones_registro.items():
            # Restaurar estilo base
            if nombre == nombre_activo:
                # Estilo para botón activo
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #3182ce, stop:1 #2b6cb0);
                        color: #ffffff; 
                        text-align: left; 
                        padding: 14px 20px;
                        border: none;
                        font-size: 13.5px; 
                        font-weight: 600; 
                        border-left: 4px solid #ed8936;
                        letter-spacing: 0.3px;
                        border-bottom: 1px solid #2d3748;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #3182ce, stop:1 #2b6cb0);
                        padding-left: 24px;
                    }
                """)
            else:
                # Restaurar estilo normal
                btn.setStyleSheet("""
                    QPushButton {
                        color: #e2e8f0; 
                        text-align: left; 
                        padding: 14px 20px;
                        border: none;
                        font-size: 13.5px; 
                        font-weight: 500;
                        background-color: transparent;
                        border-bottom: 1px solid #2d3748;
                        letter-spacing: 0.3px;
                    }
                    QPushButton:hover { 
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #2d3748, stop:1 #1a202c);
                        color: #ffffff;
                        padding-left: 24px;
                    }
                """)