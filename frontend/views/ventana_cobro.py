# frontend/views/ventana_cobro.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QGridLayout, QFrame)
from PyQt6.QtCore import Qt
import json, datetime

from frontend.components.elementos_ui import PrimaryButton, DataTable
from frontend.components.alertas import AlertaCustom
from backend.bd_conexion import DatabaseConnection

class VentanaCobro(QDialog):
    def __init__(self, folio, ws_cliente, user_data, parent=None, modo_solo_lectura=False):
        super().__init__(parent)
        self.folio = folio
        self.ws_cliente = ws_cliente
        self.user_data = user_data
        self.modo_solo_lectura = modo_solo_lectura
        self.db = DatabaseConnection()
        self.total_pagar = 0.0 # Se inicializa como float
        self.id_venta_db = None
        
        self.init_ui()
        self.cargar_detalles_orden()
        self.showMaximized()

    def init_ui(self):
        self.setWindowTitle("Detalle de Cobro" if self.modo_solo_lectura else "Procesar Pago")
        self.setStyleSheet("background-color: #f5f6fa;")
        main_layout = QHBoxLayout(self)

        # PANEL IZQUIERDO: Resumen con las nuevas columnas
        panel_izq = QFrame()
        panel_izq.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #dcdde1;")
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.addWidget(QLabel("<b>ARTÍCULOS EN LA ORDEN</b>"))
        
        self.lbl_info_general = QLabel("Cargando...")
        layout_izq.addWidget(self.lbl_info_general)

        # TABLA ACTUALIZADA SEGÚN TU PEDIDO
        self.tabla_detalles = DataTable(["Código", "Nombre", "Cant", "Desc", "Subtotal"])
        self.tabla_detalles.setEditTriggers(DataTable.EditTrigger.NoEditTriggers)
        layout_izq.addWidget(self.tabla_detalles)
        main_layout.addWidget(panel_izq, stretch=1)

        # PANEL DERECHO: Pago
        panel_der = QFrame()
        panel_der.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #dcdde1;")
        layout_der = QVBoxLayout(panel_der)
        
        self.lbl_total = QLabel("$0.00")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_total.setStyleSheet("font-size: 48px; font-weight: bold; color: #e74c3c;")
        layout_der.addWidget(QLabel("<b>TOTAL A PAGAR:</b>", alignment=Qt.AlignmentFlag.AlignCenter))
        layout_der.addWidget(self.lbl_total)

        grid_pago = QGridLayout()
        grid_pago.addWidget(QLabel("Método de Pago:"), 0, 0)
        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems(["Efectivo", "Tarjeta", "Transferencia"])
        grid_pago.addWidget(self.combo_metodo, 0, 1)

        grid_pago.addWidget(QLabel("Monto Recibido:"), 1, 0)
        self.input_recibido = QLineEdit()
        self.input_recibido.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        self.input_recibido.textChanged.connect(self.calcular_cambio)
        grid_pago.addWidget(self.input_recibido, 1, 1)
        layout_der.addLayout(grid_pago)

        self.lbl_cambio = QLabel("Cambio: $0.00")
        self.lbl_cambio.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_cambio.setStyleSheet("font-size: 24px; font-weight: bold; color: #27ae60;")
        layout_der.addWidget(self.lbl_cambio)

        layout_der.addStretch()

        self.btn_cobrar = PrimaryButton("💵 FINALIZAR COBRO")
        self.btn_cobrar.setEnabled(False)
        self.btn_cobrar.clicked.connect(self.procesar_cobro)
        
        btn_cerrar = PrimaryButton("CERRAR")
        btn_cerrar.clicked.connect(self.reject)

        if self.modo_solo_lectura:
            self.btn_cobrar.hide()
            self.input_recibido.setReadOnly(True)
            self.combo_metodo.setEnabled(False)
        
        layout_der.addWidget(self.btn_cobrar)
        layout_der.addWidget(btn_cerrar)
        main_layout.addWidget(panel_der, stretch=1)

    def cargar_detalles_orden(self):
        try:
            query = """
                SELECT v.id_venta, c.nombre_completo, e.nombre_completo, v.total,
                       co.monto_recibido, co.cambio, co.metodo_pago, emp_caja.nombre_completo as cajero
                FROM orden_venta v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                JOIN empleados e ON v.id_vendedor = e.id_empleado
                LEFT JOIN cobro_venta co ON v.id_venta = co.id_venta
                LEFT JOIN empleados emp_caja ON co.id_cajero = emp_caja.id_empleado
                WHERE v.folio = %s
            """
            res = self.db.fetch_one(query, (self.folio,))
            if res:
                # SOLUCIÓN AL ERROR DE DECIMAL: Convertimos total a float aquí
                self.id_venta_db, cliente, vendedor, total_db, rec, cam, met, cajero = res
                self.total_pagar = float(total_db) 
                
                info = f"<b>CLIENTE:</b> {cliente}<br><b>VENDEDOR:</b> {vendedor}"
                if self.modo_solo_lectura and cajero:
                    info += f"<br><b>CAJERO:</b> {cajero}<br><b>MÉTODO:</b> {met}"
                    self.input_recibido.setText(str(rec))
                    self.lbl_cambio.setText(f"Cambio entregado: ${cam}")

                self.lbl_info_general.setText(info)
                self.lbl_total.setText(f"${self.total_pagar:,.2f}")

                # CONSULTA DE PRODUCTOS SEGÚN TU CABECERA
                query_prod = """
                    SELECT p.codigo, p.nombre, d.cantidad, d.descuento, d.subtotal
                    FROM detalle_venta d
                    JOIN productos p ON d.id_producto = p.id_producto
                    WHERE d.id_venta = %s
                """
                productos = self.db.fetch_all(query_prod, (self.id_venta_db,))
                self.tabla_detalles.setRowCount(len(productos))
                from PyQt6.QtWidgets import QTableWidgetItem
                for i, p in enumerate(productos):
                    for j, val in enumerate(p):
                        self.tabla_detalles.setItem(i, j, QTableWidgetItem(str(val)))
        except Exception as e:
            print(f"Error cargando detalles: {e}")

    def calcular_cambio(self):
        if self.modo_solo_lectura: return
        try:
            # Aquí 'recibido' es float y 'self.total_pagar' ya es float
            recibido = float(self.input_recibido.text()) if self.input_recibido.text() else 0.0
            cambio = recibido - self.total_pagar
            
            if cambio >= 0:
                self.lbl_cambio.setText(f"Cambio: ${cambio:,.2f}")
                self.lbl_cambio.setStyleSheet("font-size: 24px; font-weight: bold; color: #27ae60;")
                self.btn_cobrar.setEnabled(True)
            else:
                self.lbl_cambio.setText(f"Faltan: ${abs(cambio):,.2f}")
                self.lbl_cambio.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c;")
                self.btn_cobrar.setEnabled(False)
        except ValueError: 
            pass

    def procesar_cobro(self):
        """Paso final: Guarda el registro en cobro_venta y actualiza la orden"""
        metodo = self.combo_metodo.currentText()
        recibido = float(self.input_recibido.text())
        cambio = recibido - self.total_pagar

        if AlertaCustom.ask_confirm(self, "Confirmar Cobro", f"¿Registrar pago de ${self.total_pagar:,.2f}?"):
            try:
                # 1. Actualizar estatus de la orden
                self.db.execute_query("UPDATE orden_venta SET estatus = 'Cobrada' WHERE id_venta = %s", (self.id_venta_db,))
                
                # 2. Guardar en tabla de auditoría (SIN monto_total, y usamos id_cajero como tienes en tu BD)
                query_audit = """
                    INSERT INTO cobro_venta (id_venta, monto_recibido, cambio, metodo_pago, id_cajero, fecha_cobro)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
                self.db.execute_query(query_audit, (
                    self.id_venta_db, recibido, cambio, metodo, self.user_data['id']
                ))

                self.ws_cliente.sendTextMessage(json.dumps({"tipo": "ORDEN_COBRADA", "folio": self.folio}))
                AlertaCustom.show_success(self, "Éxito", "Venta finalizada y registrada en auditoría.")
                self.accept()
            except Exception as e:
                AlertaCustom.show_error(self, "Error Fatal", f"No se pudo guardar el cobro: {e}")