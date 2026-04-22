# frontend/views/pantalla_caja.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebSockets import QWebSocket
import json

# Importaciones de nuestros componentes
from frontend.components.menu_lateral import Sidebar
from frontend.components.modulo_consulta import ModuloConsulta
from frontend.components.alertas import AlertaCustom
from frontend.views.ventana_cobro import VentanaCobro 
from frontend.views.modulo_corte import ModuloCorte
from frontend.views.apertura_caja import AperturaCajaModal
from backend.bd_conexion import DatabaseConnection


# frontend/views/pantalla_caja.py

class CajaWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.db = DatabaseConnection() 
        
        self.id_corte_activo = None
        self.fondo_inicial = 0.0
        
        # 1. PRIMERO verificamos o pedimos el fondo inicial
        self.verificar_apertura()
        
        # 2. DESPUÉS dibujamos la interfaz (ahora sí usará los $1,000)
        self.init_ui()
        
        # 3. Y al final los WebSockets
        self.ws = QWebSocket()
        self.ws.textMessageReceived.connect(self.al_recibir_notificacion)
        self.ws.open(QUrl("ws://localhost:8765"))

    def init_ui(self):
        self.setWindowTitle(f"Módulo de Caja - Cajero: {self.user_data['nombre']}")
        self.showMaximized()
        self.setStyleSheet("background-color: #f5f6fa;")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. SIDEBAR REUTILIZABLE
        # ==========================================
        opciones_menu = {
            "Órdenes Pendientes": lambda: self.cambiar_vista("Órdenes Pendientes"),
            "Ventas Cobradas": lambda: self.cambiar_vista("Ventas Cobradas"),
            "Corte de Caja": lambda: self.cambiar_vista("Corte de Caja"),
            "Cerrar Sesión": self.close
        }
        self.sidebar = Sidebar("CAJERO", opciones_menu)
        main_layout.addWidget(self.sidebar)

        # ==========================================
        # 2. ÁREA CENTRAL
        # ==========================================
        content_area = QWidget()
        self.content_layout = QVBoxLayout(content_area) 
        self.content_layout.setContentsMargins(30, 30, 30, 30)

        # --- Módulo 1: Órdenes Pendientes (La fila de cobro) ---
        query_pendientes = """
            SELECT v.folio, TO_CHAR(v.hora, 'HH24:MI'), e.nombre_completo as vendedor, c.nombre_completo as cliente, v.total
            FROM orden_venta v
            JOIN clientes c ON v.id_cliente = c.id_cliente
            JOIN empleados e ON v.id_vendedor = e.id_empleado
            WHERE v.fecha = %s AND v.estatus = 'Pendiente'
            ORDER BY v.hora ASC
        """
        menu_pendientes = {
            "Cobrar Orden": self.abrir_ventana_cobro, # <--- Sin emoji
        }


        self.modulo_pendientes = ModuloConsulta(
            titulo="FILA DE COBRO: ÓRDENES PENDIENTES", 
            columnas=["Folio", "Hora", "Vendedor", "Cliente", "Total a Pagar"], 
            query_base=query_pendientes,
            action_callback=self.abrir_ventana_cobro, # El doble clic abre el cobro
            menu_opciones=menu_pendientes
        )

        # --- Módulo 2: Historial de Cobros del Día ---
        query_cobradas = """
            SELECT v.folio, TO_CHAR(v.hora, 'HH24:MI'), c.nombre_completo, v.total, v.estatus
            FROM orden_venta v
            JOIN clientes c ON v.id_cliente = c.id_cliente
            WHERE v.fecha = %s AND v.estatus = 'Cobrada'
            ORDER BY v.hora DESC
        """
        menu_cobradas = {
            "Ver Detalles": self.ver_detalle_cobrada, # <--- Sin emoji y texto corto
            "Reimprimir": self.reimprimir_ticket      # <--- Sin emoji y texto corto
        }

        self.modulo_cobradas = ModuloConsulta(
            titulo="HISTORIAL DE VENTAS COBRADAS HOY", 
            columnas=["Folio", "Hora", "Cliente", "Total", "Estatus"], 
            query_base=query_cobradas,
            menu_opciones=menu_cobradas
        )

        self.modulo_corte = ModuloCorte(self.user_data, self.id_corte_activo, self.fondo_inicial)
        self.content_layout.addWidget(self.modulo_corte)
        self.modulo_corte.hide()

        # Añadimos los módulos al layout
        self.content_layout.addWidget(self.modulo_pendientes)
        self.content_layout.addWidget(self.modulo_cobradas)
        
        # Estado inicial
        self.modulo_cobradas.hide()
        self.sidebar.resaltar_boton("Órdenes Pendientes")

        main_layout.addWidget(content_area)

    # ==========================================
    # LÓGICA DE INTERFAZ
    # ==========================================
    def cambiar_vista(self, vista):
        self.sidebar.resaltar_boton(vista)
        
        self.modulo_pendientes.hide()
        self.modulo_cobradas.hide()
        self.modulo_corte.hide()

        if vista == "Órdenes Pendientes":
            self.modulo_pendientes.show()
            self.modulo_pendientes.cargar_datos_del_dia()
        elif vista == "Ventas Cobradas":
            self.modulo_cobradas.show()
            self.modulo_cobradas.cargar_datos_del_dia()
        elif vista == "Corte de Caja":
            self.modulo_corte.show()
            self.modulo_corte.cargar_totales() # <-- Al entrar, va a Postgres a traer los totales nuevos

    # ==========================================
    # FUNCIONES DEL CAJERO
    # ==========================================
    def abrir_ventana_cobro(self, folio):
        """Modo Cobrar: Le pasamos self.user_data para saber quién cobra"""
        # IMPORTANTE: Pasamos self.user_data (el diccionario del cajero)
        dialog = VentanaCobro(folio, self.ws, self.user_data, self, modo_solo_lectura=False)
        if dialog.exec():
            self.modulo_pendientes.cargar_datos_del_dia()
            self.modulo_cobradas.cargar_datos_del_dia()

    def reimprimir_ticket(self, folio):
        """Lógica para mandar a la impresora térmica"""
        AlertaCustom.show_info(self, "Imprimiendo", f"Enviando el ticket del folio {folio} a la impresora térmica...")

    def al_recibir_notificacion(self, mensaje):
        """Escucha los eventos del WebSocket y recarga la tabla sola"""
        datos = json.loads(mensaje)
        if datos["tipo"] == "NUEVA_ORDEN":
            AlertaCustom.show_info(self, "Nueva Orden", f"Fila actualizada. Nueva orden de {datos.get('vendedor', 'Vendedor')}.")
            self.modulo_pendientes.cargar_datos_del_dia()
        elif datos["tipo"] == "ORDEN_COBRADA":
            self.modulo_pendientes.cargar_datos_del_dia()
            self.modulo_cobradas.cargar_datos_del_dia()

    def ver_detalle_cobrada(self, folio):
        """Modo Auditoría: Ver detalles de una venta ya cobrada"""
        # Pasamos modo_solo_lectura=True
        dialog = VentanaCobro(folio, self.ws, self.user_data, self, modo_solo_lectura=True)
        dialog.exec()
    
    def verificar_apertura(self):
        """Revisa si el cajero ya tiene un turno abierto. Si no, lo obliga a abrirlo."""
        query = "SELECT id_corte, fondo_inicial FROM cortes_caja WHERE id_cajero = %s AND estatus = 'Abierta'"
        res = self.db.fetch_one(query, (self.user_data['id'],))

        if self.user_data.get('rol') == 'Administrador':
            # El admin solo observa, no necesita un id_corte activo para ver las tablas
            return
        
        if res:
            # Ya tenía un turno abierto (ej. se le cerró el programa y volvió a entrar)
            self.id_corte_activo, self.fondo_inicial = res[0], float(res[1])
        else:
            # Obligamos a abrir caja
            modal = AperturaCajaModal(self.user_data['id'], self)
            if modal.exec():
                self.id_corte_activo = modal.id_corte_generado
                self.fondo_inicial = modal.fondo_ingresado
            else:
                # Si cierra la ventanita con la "X" sin abrir caja, cerramos el programa
                self.close()