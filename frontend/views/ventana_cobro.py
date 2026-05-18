# frontend/views/ventana_cobro.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QGridLayout, QFrame)
from PyQt6.QtCore import Qt
import json, datetime
import qtawesome as qta

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
        self.total_pagar = 0.0 
        self.id_venta_db = None
        
        self.init_ui()
        self.cargar_detalles_orden()
        self.showMaximized()

    def init_ui(self):
        self.setWindowTitle("Detalle de Cobro" if self.modo_solo_lectura else "Procesar Pago")
        self.setStyleSheet("background-color: #f1f5f9;")
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        # PANEL IZQUIERDO
        panel_izq = QFrame()
        panel_izq.setStyleSheet("background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;")
        layout_izq = QVBoxLayout(panel_izq)
        layout_izq.setContentsMargins(20, 20, 20, 20)
        layout_izq.setSpacing(15)
        
        lbl_titulo_izq = QLabel("ARTÍCULOS EN LA ORDEN")
        lbl_titulo_izq.setStyleSheet("font-size: 16px; font-weight: 800; color: #1e293b;")
        layout_izq.addWidget(lbl_titulo_izq)
        
        self.lbl_info_general = QLabel("Cargando...")
        self.lbl_info_general.setStyleSheet("font-size: 14px; color: #475569; line-height: 1.5;")
        layout_izq.addWidget(self.lbl_info_general)

   
        self.tabla_detalles = DataTable(["Código", "Nombre", "Cant", "Desc", "Subtotal"])
        self.tabla_detalles.setEditTriggers(DataTable.EditTrigger.NoEditTriggers)
        layout_izq.addWidget(self.tabla_detalles)
        main_layout.addWidget(panel_izq, stretch=6)

        # PANEL DERECHO
        panel_der = QFrame()
        panel_der.setStyleSheet("background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0;")
        layout_der = QVBoxLayout(panel_der)
        layout_der.setContentsMargins(24, 24, 24, 24)
        layout_der.setSpacing(20)
        
        lbl_titulo_der = QLabel("TOTAL A PAGAR")
        lbl_titulo_der.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo_der.setStyleSheet("font-size: 14px; font-weight: 800; color: #64748b; letter-spacing: 1px;")
        layout_der.addWidget(lbl_titulo_der)

        self.lbl_total = QLabel("$0.00")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_total.setStyleSheet("font-size: 54px; font-weight: 900; color: #0f172a;")
        layout_der.addWidget(self.lbl_total)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #e2e8f0; max-height: 1px; margin: 10px 0px;")
        layout_der.addWidget(sep)

        grid_pago = QGridLayout()
        grid_pago.setSpacing(15)
        
        lbl_metodo = QLabel("Método de Pago:")
        lbl_metodo.setStyleSheet("font-weight: 700; color: #334155;")
        grid_pago.addWidget(lbl_metodo, 0, 0)
        
        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems(["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia"])
        self.combo_metodo.setStyleSheet("""
            QComboBox {
                padding: 12px; font-size: 14px; color: #1e293b;
                background-color: #f8fafc; border: 2px solid #e2e8f0; border-radius: 8px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox:focus { border: 2px solid #3b82f6; background-color: #ffffff; }
        """)
        grid_pago.addWidget(self.combo_metodo, 0, 1)

        lbl_recibido = QLabel("Monto Recibido:")
        lbl_recibido.setStyleSheet("font-weight: 700; color: #334155;")
        grid_pago.addWidget(lbl_recibido, 1, 0)
        
        self.input_recibido = QLineEdit()
        self.input_recibido.setPlaceholderText("0.00")
        self.input_recibido.setStyleSheet("""
            QLineEdit {
                font-size: 24px; font-weight: bold; padding: 12px; color: #0f172a;
                background-color: #f8fafc; border: 2px solid #e2e8f0; border-radius: 8px;
            }
            QLineEdit:focus { border: 2px solid #3b82f6; background-color: #ffffff; }
        """)
        self.input_recibido.textChanged.connect(self.calcular_cambio)
        grid_pago.addWidget(self.input_recibido, 1, 1)
        layout_der.addLayout(grid_pago)

        self.lbl_cambio = QLabel("Cambio: $0.00")
        self.lbl_cambio.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_cambio.setStyleSheet("font-size: 28px; font-weight: 900; color: #10b981; margin-top: 10px;")
        layout_der.addWidget(self.lbl_cambio)

        layout_der.addStretch()

        self.btn_cobrar = PrimaryButton("  FINALIZAR COBRO")
        self.btn_cobrar.setIcon(qta.icon('fa5s.check-circle', color='white'))
        self.btn_cobrar.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: white; padding: 18px; 
                font-size: 16px; font-weight: 800; border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #059669; }
            QPushButton:disabled { background-color: #94a3b8; }
        """)
        self.btn_cobrar.setEnabled(False)
        self.btn_cobrar.clicked.connect(self.procesar_cobro)
        
        btn_cerrar = PrimaryButton("  CERRAR")
        btn_cerrar.setIcon(qta.icon('fa5s.times', color='#64748b'))
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #64748b; padding: 14px; 
                font-size: 14px; font-weight: 700; border: 2px solid #e2e8f0; border-radius: 8px;
            }
            QPushButton:hover { background-color: #f1f5f9; color: #334155; border: 2px solid #cbd5e1; }
        """)
        btn_cerrar.clicked.connect(self.reject)

        if self.modo_solo_lectura:
            self.btn_cobrar.hide()
            self.input_recibido.setReadOnly(True)
            self.combo_metodo.setEnabled(False)
        
        layout_der.addWidget(self.btn_cobrar)
        layout_der.addWidget(btn_cerrar)
        main_layout.addWidget(panel_der, stretch=4)

    def cargar_detalles_orden(self):
        try:
            # 1. Agregamos v.cliente_temporal al final del SELECT
            query = """
                SELECT v.id_venta, c.nombre_completo, e.nombre_completo, v.total,
                       co.monto_recibido, co.cambio, co.metodo_pago, emp_caja.nombre_completo as cajero, v.cliente_temporal
                FROM orden_venta v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                JOIN empleados e ON v.id_vendedor = e.id_empleado
                LEFT JOIN cobro_venta co ON v.id_venta = co.id_venta
                LEFT JOIN empleados emp_caja ON co.id_cajero = emp_caja.id_empleado
                WHERE v.folio = %s
            """
            res = self.db.fetch_one(query, (self.folio,))
            if res:
                # 2. Desempaquetamos la nueva variable cte_temp
                self.id_venta_db, cliente, vendedor, total_db, rec, cam, met, cajero, cte_temp = res
                self.total_pagar = float(total_db) 
                
                # 3. Armamos el nombre a mostrar
                if cte_temp and cte_temp != 'MOSTRADOR':
                    nombre_mostrar = f"{cliente} ({cte_temp})"
                else:
                    nombre_mostrar = cliente

                # 4. Inyectamos el nombre_mostrar en la etiqueta
                info = f"<span style='color: #64748b; font-size: 12px; font-weight: bold;'>CLIENTE</span><br><span style='font-size: 16px; font-weight: 600; color: #0f172a;'>{nombre_mostrar}</span><br><br><span style='color: #64748b; font-size: 12px; font-weight: bold;'>VENDEDOR</span><br><span style='font-size: 16px; font-weight: 600; color: #0f172a;'>{vendedor}</span>"
                if self.modo_solo_lectura and cajero:
                    info += f"<br><br><span style='color: #64748b; font-size: 12px; font-weight: bold;'>CAJERO</span><br><span style='font-size: 16px; font-weight: 600; color: #0f172a;'>{cajero}</span><br><br><span style='color: #64748b; font-size: 12px; font-weight: bold;'>MÉTODO</span><br><span style='font-size: 16px; font-weight: 600; color: #0f172a;'>{met}</span>"
                    self.input_recibido.setText(str(rec))
                    self.lbl_cambio.setText(f"Cambio entregado: ${cam}")

                self.lbl_info_general.setText(info)
                self.lbl_total.setText(f"${self.total_pagar:,.2f}")

                # CONSULTA DE PRODUCTOS 
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
                self.lbl_cambio.setStyleSheet("font-size: 28px; font-weight: 900; color: #10b981; margin-top: 10px;")
                self.btn_cobrar.setEnabled(True)
            else:
                self.lbl_cambio.setText(f"Faltan: ${abs(cambio):,.2f}")
                self.lbl_cambio.setStyleSheet("font-size: 28px; font-weight: 900; color: #ef4444; margin-top: 10px;")
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
                
                # 2. Guardar en tabla de auditoría
                query_audit = """
                    INSERT INTO cobro_venta (id_venta, monto_recibido, cambio, metodo_pago, id_cajero, fecha_cobro)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """
                self.db.execute_query(query_audit, (
                    self.id_venta_db, recibido, cambio, metodo, self.user_data['id']
                ))

              
                self.generar_y_abrir_ticket(recibido, cambio, metodo)

                self.ws_cliente.sendTextMessage(json.dumps({"tipo": "ORDEN_COBRADA", "folio": self.folio}))
                AlertaCustom.show_success(self, "Éxito", "Venta finalizada y ticket emitido correctamente.")
                self.accept()
            except Exception as e:
                AlertaCustom.show_error(self, "Error Fatal", f"No se pudo guardar el cobro: {e}")

    def generar_y_abrir_ticket(self, recibido, cambio, metodo):
        """Función auxiliar para construir el diccionario de datos del ticket y abrirlo"""
        import os, sys
        from backend.generador_pdf import GeneradorPDF
        try:
    
            query = """
                SELECT v.folio, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), c.nombre_completo, v.cliente_temporal, v.total
                FROM orden_venta v
                JOIN clientes c ON v.id_cliente = c.id_cliente
                WHERE v.id_venta = %s
            """
            res = self.db.fetch_one(query, (self.id_venta_db,))
            if not res: return
            
            folio, fecha, hora, cliente, cte_temp, total = res
            nombre_cliente = f"{cliente} ({cte_temp})" if cte_temp and cte_temp != 'MOSTRADOR' else cliente

            query_prod = """
                SELECT p.codigo, p.nombre, d.cantidad, d.descuento, d.precio_unitario, d.subtotal
                FROM detalle_venta d
                JOIN productos p ON d.id_producto = p.id_producto
                WHERE d.id_venta = %s
            """
            productos_db = self.db.fetch_all(query_prod, (self.id_venta_db,))
            
            datos_ticket = {
                "folio": folio,
                "fecha": str(fecha),
                "hora": hora,
                "cajero": self.user_data['nombre'],
                "cliente": nombre_cliente,
                "productos": productos_db, 
                "total": float(total),
                "recibido": recibido,
                "cambio": cambio,
                "metodo": metodo
            }

            carpeta_tickets = os.path.join(os.getcwd(), "tickets")
            os.makedirs(carpeta_tickets, exist_ok=True)
            ruta_salida = os.path.join(carpeta_tickets, f"Ticket_{folio}.pdf")

            pdf = GeneradorPDF()
            pdf.generar_ticket_venta(datos_ticket, ruta_salida)

            # Apertura del sistema del visor de Windows/Mac
            if sys.platform == "win32":
                os.startfile(ruta_salida)
            else:
                import subprocess
                subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", ruta_salida])
        except Exception as e:
            print(f"Error generando ticket en cobro: {e}")