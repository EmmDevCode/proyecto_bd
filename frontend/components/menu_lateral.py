# frontend/components/sidebar.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QFrame, QScrollArea, QLabel)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve

class MenuColapsable(QWidget):
    """Componente personalizado para un menú con animación de acordeón"""
    def __init__(self, titulo, icono=None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.titulo_base = titulo
        
        # Botón toggle
        self.btn_toggle = QPushButton(f"▶  {self.titulo_base}")
        
        if icono:
            self.btn_toggle.setIcon(icono)
            
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                color: #94a3b8; 
                text-align: left; 
                padding: 14px 20px;
                font-weight: 600; 
                border: none; 
                font-size: 13px;
                background-color: transparent;
                border-radius: 8px;
                margin: 2px 10px;
            }
            QPushButton:hover { 
                background-color: #1e293b;
                color: #f8fafc;
            }
        """)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.animar_toggle)
        self.layout.addWidget(self.btn_toggle)

        self.area_contenido = QFrame()
        self.area_contenido.setStyleSheet("""
            background-color: transparent;
            border-left: 2px solid #334155;
            margin-left: 24px;
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
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
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
                color: #f8fafc; 
                font-size: 22px; 
                font-weight: 800;
                padding: 30px 10px; 
                background-color: #0f172a;
                border-bottom: 1px solid #1e293b;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-family: 'Segoe UI', system-ui, sans-serif;
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
        self.botones_registro.clear()
        
        while self.layout_scroll.count():
            child = self.layout_scroll.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.limpiar_layout(child.layout())
        
        for clave, opciones in config_menu.items():
            
            # 1. Separamos si la clave es una tupla (icono, texto) o solo texto
            if isinstance(clave, tuple):
                icono_obj, titulo = clave
            else:
                icono_obj, titulo = None, clave

            if isinstance(opciones, dict):
                # Pasamos el icono al submenú
                menu_animado = MenuColapsable(titulo, icono=icono_obj) 
                for nombre, funcion in opciones.items():
                    btn = self.crear_boton(nombre, funcion, es_sub=True)
                    menu_animado.agregar_boton(btn)
                    self.botones_registro[nombre] = btn
                menu_animado.inicializar_altura()
                self.layout_scroll.addWidget(menu_animado)
            else:
                # Pasamos el icono al botón normal
                btn = self.crear_boton(titulo, opciones, es_sub=False, icono=icono_obj)
                self.layout_scroll.addWidget(btn)
                self.botones_registro[titulo] = btn
        
        self.layout_scroll.addStretch()

    def limpiar_layout(self, layout):
        """Limpia recursivamente un layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.limpiar_layout(child.layout())

    def crear_boton(self, texto, funcion, es_sub, icono=None):
        """Crea un botón con el estilo apropiado"""
        
        btn = QPushButton(f"  {texto}" if es_sub else f"  {texto}")
        btn.setProperty("es_sub", es_sub)
        
        # Le aplicamos el icono si existe
        if icono:
            btn.setIcon(icono)
            
        if es_sub:
            btn.setStyleSheet("""
                QPushButton {
                    color: #94a3b8; 
                    text-align: left; 
                    padding: 10px 15px 10px 20px;
                    margin: 2px 10px 2px 0px;
                    border: none;
                    font-size: 13px; 
                    background-color: transparent;
                    border-radius: 6px;
                }
                QPushButton:hover { 
                    background-color: #1e293b; 
                    color: #f8fafc;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    color: #94a3b8; 
                    text-align: left; 
                    padding: 14px 20px;
                    margin: 2px 10px;
                    border: none;
                    font-size: 14px; 
                    font-weight: 600;
                    background-color: transparent;
                    border-radius: 8px;
                    letter-spacing: 0.3px;
                }
                QPushButton:hover { 
                    background-color: #1e293b;
                    color: #f8fafc;
                }
                QPushButton:pressed {
                    background-color: #0f172a;
                }
            """)
        
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if funcion: 
            btn.clicked.connect(funcion)
        return btn

    def resaltar_boton(self, nombre_activo):
        """Cambia el estilo del botón seleccionado"""
        for nombre, btn in self.botones_registro.items():
            es_sub = btn.property("es_sub")
            if nombre == nombre_activo:
                if es_sub:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3b82f6; color: #ffffff; text-align: left; 
                            padding: 10px 15px 10px 20px; margin: 2px 10px 2px 0px;
                            border: none; font-size: 13px; font-weight: 700; border-radius: 6px;
                        }
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3b82f6; color: #ffffff; text-align: left; 
                            padding: 14px 20px; margin: 2px 10px; border: none;
                            font-size: 14px; font-weight: 700; border-radius: 8px; letter-spacing: 0.3px;
                        }
                    """)
            else:
                if es_sub:
                    btn.setStyleSheet("""
                        QPushButton {
                            color: #94a3b8; text-align: left; padding: 10px 15px 10px 20px;
                            margin: 2px 10px 2px 0px; border: none; font-size: 13px; 
                            background-color: transparent; border-radius: 6px;
                        }
                        QPushButton:hover { background-color: #1e293b; color: #f8fafc; }
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            color: #94a3b8; text-align: left; padding: 14px 20px; margin: 2px 10px;
                            border: none; font-size: 14px; font-weight: 600;
                            background-color: transparent; border-radius: 8px; letter-spacing: 0.3px;
                        }
                        QPushButton:hover { background-color: #1e293b; color: #f8fafc; }
                    """)