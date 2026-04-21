# frontend/views/crear_cotizacion.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidgetItem, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWebSockets import QWebSocket
import json
import datetime

from frontend.components.elementos_ui import FormInput, PrimaryButton, DataTable
from backend.bd_conexion import DatabaseConnection
from frontend.components.buscador import GenericSearchModal

class CreateQuotationWindow(QDialog):
    def __init__(self, user_data, parent=None, folio_editar=None):
        super().__init__(parent)
        self.user_data = user_data
        self.folio_editar = folio_editar
        self.id_cot_actual = None
        self.modo_edicion_activo = False
        self.db = DatabaseConnection()
        self.carrito = [] 
        
        # WebSocket para avisar de cambios
        self.ws_cliente = QWebSocket()
        self.ws_cliente.open(QUrl("ws://localhost:8765"))
        
        self.init_ui()
        self.setup_shortcuts()
        
        if self.folio_editar:
            self.cargar_datos_para_edicion()

    def init_ui(self):
        titulo = f"VISTA PREVIA COTIZACIÓN: {self.folio_editar}" if self.folio_editar else "Nueva Cotización"
        self.setWindowTitle(f"{titulo} - El Tornillo Feliz")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Sección superior (Igual a tu diseño pero para COT) ---
        top_layout = QHBoxLayout()
        info_grid = QGridLayout()
        
        info_grid.addWidget(QLabel("<b>CLIENTE</b>"), 0, 0)
        self.input_cliente = QLineEdit("Venta mostrador")
        self.input_cliente.setReadOnly(True)
        self.input_cliente.setStyleSheet("background-color: #dcdde1; padding: 5px;")
        info_grid.addWidget(self.input_cliente, 0, 1)

        info_grid.addWidget(QLabel("<b>FOLIO</b>"), 0, 2)
        self.input_folio = QLineEdit("Generando...")
        self.input_folio.setReadOnly(True)
        self.input_folio.setStyleSheet("background-color: #dcdde1;")
        info_grid.addWidget(self.input_folio, 0, 3)

        top_layout.addLayout(info_grid)
        layout.addLayout(top_layout)

        # Buscador F2
        self.search_input = FormInput("Buscar producto para cotizar f2")
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        layout.addWidget(self.search_input)

        # Tabla Carrito
        self.tabla_carrito = DataTable(["", "codigo", "Producto", "Cant.", "desc", "Precio U.", "Subtotal"])
        self.tabla_carrito.itemChanged.connect(self.recalcular_totales_por_edicion)
        layout.addWidget(self.tabla_carrito)

        # Footer
        footer = QHBoxLayout()
        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.btn_guardar = PrimaryButton("GUARDAR COTIZACIÓN")
        self.btn_guardar.clicked.connect(self.save_quotation)
        
        self.btn_editar = PrimaryButton("✏️ Editar Cotización")
        self.btn_editar.setStyleSheet("background-color: #f39c12; color: white;")
        self.btn_editar.clicked.connect(self.desbloquear_edicion)
        self.btn_editar.hide()

        footer.addWidget(self.lbl_total)
        footer.addStretch()
        footer.addWidget(self.btn_editar)
        footer.addWidget(self.btn_guardar)
        layout.addLayout(footer)

    def setup_shortcuts(self):
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        self.shortcut_f2.activated.connect(self.search_input.setFocus)

    def cargar_datos_para_edicion(self):
        """Carga datos exclusivos de la tabla cotizaciones [cite: 561]"""
        try:
            query = """
                SELECT id_cotizacion, c.nombre_completo, fecha, TO_CHAR(hora, 'HH24:MI'), total
                FROM cotizaciones v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                WHERE v.folio = %s
            """
            res = self.db.fetch_one(query, (self.folio_editar,))
            if res:
                self.id_cot_actual, cliente, fecha, hora, total = res
                self.input_folio.setText(self.folio_editar)
                self.input_cliente.setText(cliente)
                
                # Cargar productos de detalle_cotizacion [cite: 566]
                query_det = """
                    SELECT p.id_producto, p.codigo, p.nombre, d.cantidad, d.descuento, d.precio_unitario, d.subtotal
                    FROM detalle_cotizacion d
                    JOIN productos p ON d.id_producto = p.id_producto
                    WHERE d.id_cotizacion = %s
                """
                detalles = self.db.fetch_all(query_det, (self.id_cot_actual,))
                for d in detalles:
                    self.carrito.append({
                        "id": d[0], "codigo": d[1], "nombre": d[2],
                        "cant": float(d[3]), "desc": float(d[4]),
                        "precio": float(d[5]), "subtotal": float(d[6])
                    })
                self.update_cart_table()
                self.bloquear_interfaz()
                self.btn_editar.show()
        except Exception as e:
            print(f"Error cargando cotización: {e}")

    def bloquear_interfaz(self):
        self.search_input.setEnabled(False)
        self.btn_guardar.setEnabled(False)
        self.tabla_carrito.setEditTriggers(DataTable.EditTrigger.NoEditTriggers)

    def desbloquear_edicion(self):
        self.modo_edicion_activo = True
        self.search_input.setEnabled(True)
        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText("GUARDAR CAMBIOS")
        self.btn_editar.hide()
        self.tabla_carrito.setEditTriggers(DataTable.EditTrigger.DoubleClicked)

    def save_quotation(self):
        """Guarda o actualiza en las tablas de cotización """
        try:
            now = datetime.datetime.now()
            total = sum(p['subtotal'] for p in self.carrito)
            hora = now.strftime('%H:%M')

            if self.folio_editar and self.modo_edicion_activo:
                # UPDATE
                self.db.execute_query("UPDATE cotizaciones SET total = %s, hora = %s WHERE id_cotizacion = %s", 
                                      (total, hora, self.id_cot_actual))
                self.db.execute_query("DELETE FROM detalle_cotizacion WHERE id_cotizacion = %s", (self.id_cot_actual,))
                id_final = self.id_cot_actual
                folio_final = self.folio_editar
            else:
                # INSERT
                folio_final = f"COT-{now.strftime('%Y%m%d%H%M%S')}"
                query = "INSERT INTO cotizaciones (folio, id_vendedor, fecha, hora, id_cliente, total) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_cotizacion"
                id_final = self.db.fetch_one(query, (folio_final, self.user_data['id'], now.date(), hora, 1, total))[0]

            query_ins = "INSERT INTO detalle_cotizacion (id_cotizacion, id_producto, cantidad, precio_unitario, descuento, subtotal) VALUES (%s, %s, %s, %s, %s, %s)"
            for p in self.carrito:
                self.db.execute_query(query_ins, (id_final, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

            self.ws_cliente.sendTextMessage(json.dumps({"tipo": "NUEVA_COTIZACION", "folio": folio_final}))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")
            
    # (Incluye aquí tus funciones de procesar_busqueda, update_cart_table y recalcular_totales...)