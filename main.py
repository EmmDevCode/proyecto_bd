# main.py
import sys
from PyQt6.QtWidgets import QApplication
from frontend.views.ventana_login import LoginWindow
from frontend.views.pantalla_carga import LoadingScreen
from frontend.views.pantalla_vendedor import PosWindow 
from frontend.assets.styles import LIGHT_THEME

class AppController:
    def __init__(self):
        self.login_window = None
        self.loading_screen = None
        self.main_window = None
        self.show_login()

    def show_login(self):
        """Paso 1: Mostrar Login"""
        self.login_window = LoginWindow()
        self.login_window.setStyleSheet(LIGHT_THEME)
        # Conectamos la señal personalizada que crearemos en el Login
        self.login_window.login_success.connect(self.show_loading)
        self.login_window.show()

    def show_loading(self, user_data):
        """Paso 2: Mostrar Pantalla de Carga y verificar conexión"""
        self.login_window.close()
        self.loading_screen = LoadingScreen(user_data)
        self.loading_screen.setStyleSheet(LIGHT_THEME)
        # Cuando la carga termine, llamamos al ruteador de roles
        self.loading_screen.connection_ready.connect(self.route_by_role)
        self.loading_screen.show()

    def route_by_role(self, user_data):
        """Paso 3: Abrir la ventana correcta según el Rol [cite: 866]"""
        self.loading_screen.close()
        role = user_data['rol']
        
        if role == 'Vendedor':
            self.main_window = PosWindow(user_data)
        elif role == 'Cajero':
            # self.main_window = CajaWindow(user_data) (Por crear)
            print("Abriendo Módulo de Caja...")
        elif role == 'Administrador':
            # self.main_window = AdminWindow(user_data) (Por crear)
            print("Abriendo Módulo Administrativo (ERP)...")
            
        if self.main_window:
            self.main_window.setStyleSheet(LIGHT_THEME)
            self.main_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(LIGHT_THEME)
    controller = AppController()
    sys.exit(app.exec())