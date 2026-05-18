# frontend/views/crear_cotizacion.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut, QImage, QPixmap
from PyQt6.QtWebSockets import QWebSocket
import json
import datetime
import os
import sys
import fitz  
from frontend.components.elementos_ui import FormInput, PrimaryButton
from frontend.components.carrito_manejador import CarritoManager
from frontend.components.alertas import AlertaCustom
from frontend.components.buscador import GenericSearchModal
from backend.bd_conexion import DatabaseConnection
from backend.generador_pdf import GeneradorPDF

class CreateQuotationWindow(QDialog):
    def __init__(self, user_data, parent=None, folio_editar=None):
        super().__init__(parent)
        self.user_data = user_data
        self.folio_editar = folio_editar
        self.id_cot_actual = None
        self.modo_edicion_activo = False
        self.db = DatabaseConnection()
        
        self.ws_cliente = QWebSocket()
        self.ws_cliente.open(QUrl("ws://localhost:8765"))
        
        self.init_ui()
        self.setup_shortcuts()
        
        if self.folio_editar:
            self.cargar_datos_para_edicion()

    def init_ui(self):
        if self.folio_editar:
            self.setWindowTitle(f"VISTA PREVIA COTIZACIÓN: {self.folio_editar}")
        else:
            self.setWindowTitle("Nueva Cotización - El Tornillo Feliz")
            
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setStyleSheet("background-color: #f1f5f9;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        def crear_tarjeta():
            tarjeta = QFrame()
            tarjeta.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; }")
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(Qt.GlobalColor.lightGray)
            shadow.setOffset(0, 2)
            tarjeta.setGraphicsEffect(shadow)
            return tarjeta

        # --- 1. ENCABEZADO ---
        card_info = crear_tarjeta()
        info_layout = QVBoxLayout(card_info)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        titulo_info = QLabel("DATOS DE LA COTIZACIÓN")
        titulo_info.setStyleSheet("font-size: 11pt; font-weight: 800; color: #475569; border: none;")
        info_layout.addWidget(titulo_info)

        header_grid = QGridLayout()
        header_grid.setSpacing(10)
        
        lbl_cliente = QLabel("CLIENTE:")
        lbl_cliente.setStyleSheet("font-weight: bold; color: #64748b; border: none;")
        header_grid.addWidget(lbl_cliente, 0, 0)
        self.input_cliente = QLineEdit("Venta mostrador")
        self.input_cliente.setReadOnly(True)
        self.input_cliente.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; color: #334155; font-weight: bold;")
        header_grid.addWidget(self.input_cliente, 0, 1)

        lbl_folio = QLabel("FOLIO:")
        lbl_folio.setStyleSheet("font-weight: bold; color: #64748b; border: none;")
        header_grid.addWidget(lbl_folio, 0, 2)
        self.input_folio = QLineEdit(self.folio_editar if self.folio_editar else "AUTO-GENERADO")
        self.input_folio.setReadOnly(True)
        self.input_folio.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; color: #334155; font-weight: bold;")
        header_grid.addWidget(self.input_folio, 0, 3)

        info_layout.addLayout(header_grid)
        main_layout.addWidget(card_info)

        # --- 2. CARRITO ---
        card_carrito = crear_tarjeta()
        carrito_layout = QVBoxLayout(card_carrito)
        carrito_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_carrito = QLabel("DETALLE DE ARTÍCULOS")
        lbl_carrito.setStyleSheet("font-size: 11pt; font-weight: 800; color: #475569; border: none;")
        carrito_layout.addWidget(lbl_carrito)

        self.search_input = FormInput("F2 - Escribe el nombre o código del producto para cotizar...")
        self.search_input.setStyleSheet("QLineEdit { border: 2px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 12pt; background-color: #f8fafc; } QLineEdit:focus { border: 2px solid #3b82f6; background-color: #ffffff; }")
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        carrito_layout.addWidget(self.search_input)

        self.carrito_manager = CarritoManager()
        self.carrito_manager.setStyleSheet("border: none;")
        carrito_layout.addWidget(self.carrito_manager)
        
        main_layout.addWidget(card_carrito, stretch=1)

        # --- 3. FOOTER ---
        card_footer = crear_tarjeta()
        card_footer.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; border-top: 4px solid #3b82f6; }")
        footer_layout = QHBoxLayout(card_footer)
        footer_layout.setContentsMargins(20, 15, 20, 15)
        
        btn_cancelar = QPushButton("CANCELAR")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 10pt; } QPushButton:hover { background-color: #dc2626; }")
        btn_cancelar.clicked.connect(self.reject)

        self.btn_imprimir = QPushButton("🖨️ IMPRIMIR PDF")
        self.btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_imprimir.setStyleSheet("QPushButton { background-color: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 10pt; } QPushButton:hover { background-color: #2563eb; }")
        self.btn_imprimir.clicked.connect(self.exportar_cotizacion_pdf)

        self.btn_habilitar_edicion = QPushButton("✏️ EDITAR COTIZACIÓN")
        self.btn_habilitar_edicion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_habilitar_edicion.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 10pt; } QPushButton:hover { background-color: #d97706; }")
        self.btn_habilitar_edicion.clicked.connect(self.desbloquear_edicion)
        self.btn_habilitar_edicion.hide()

        self.btn_convertir = QPushButton("💵 CONVERTIR A VENTA")
        self.btn_convertir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convertir.setStyleSheet("QPushButton { background-color: #8b5cf6; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 10pt; } QPushButton:hover { background-color: #7c3aed; }")
        self.btn_convertir.clicked.connect(self.convertir_a_venta)
        self.btn_convertir.hide()

        self.btn_guardar = QPushButton("GUARDAR COTIZACIÓN (F3)")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet("QPushButton { background-color: #10b981; color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: 800; font-size: 11pt; } QPushButton:hover { background-color: #059669; }")
        self.btn_guardar.clicked.connect(self.save_quotation)

        footer_layout.addWidget(btn_cancelar)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_imprimir)
        footer_layout.addWidget(self.btn_convertir)
        footer_layout.addWidget(self.btn_habilitar_edicion)
        footer_layout.addWidget(self.btn_guardar)
        
        main_layout.addWidget(card_footer)

    def exportar_cotizacion_pdf(self):
        productos, total = self.carrito_manager.obtener_datos()
        if not productos:
            AlertaCustom.show_error(self, "Carrito Vacío", "No hay artículos para generar el PDF.")
            return

        folio_str = self.input_folio.text()
        if folio_str == "AUTO-GENERADO":
            folio_str = "SIN-GUARDAR"

        datos = {
            "folio": folio_str,
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
            "cliente": self.input_cliente.text(),
            "vendedor": self.user_data['nombre'],
            "productos": [],
            "total": total
        }

        for p in productos:
            datos["productos"].append([p["codigo"], p["nombre"], p["cant"], p["desc"], p["precio"], p["subtotal"]])

        
        directorio_base = os.getcwd() 
        carpeta_cotizaciones = os.path.join(directorio_base, "cotizaciones")
        os.makedirs(carpeta_cotizaciones, exist_ok=True)
        
        nombre_archivo = f"Cotizacion_{folio_str}.pdf"
        ruta_salida = os.path.join(carpeta_cotizaciones, nombre_archivo)

        try:
            pdf = GeneradorPDF()
            pdf.generar_cotizacion(datos, ruta_salida)
            
            
            visor = VisorCotizacionModal(ruta_salida, datos, self)
            visor.exec()
                
        except Exception as e:
            AlertaCustom.show_error(self, "Error PDF", f"Hubo un problema al crear el PDF: {e}")

    def setup_shortcuts(self):
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        self.shortcut_f2.activated.connect(self.search_input.setFocus)
        self.shortcut_f3 = QShortcut(QKeySequence(Qt.Key.Key_F3), self)
        self.shortcut_f3.activated.connect(self.save_quotation)

    def bloquear_interfaz(self):
        self.search_input.setEnabled(False)
        self.btn_guardar.setEnabled(False)
        self.carrito_manager.bloquear_edicion()

    def desbloquear_edicion(self):
        self.modo_edicion_activo = True
        self.setWindowTitle(f"EDITANDO COTIZACIÓN: {self.folio_editar}")
        self.search_input.setEnabled(True)
        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText("GUARDAR CAMBIOS")
        self.btn_guardar.setStyleSheet("QPushButton { background-color: #10b981; color: white; border: none; padding: 12px 30px; border-radius: 8px; font-weight: 800; font-size: 11pt; } QPushButton:hover { background-color: #059669; }")
        self.btn_habilitar_edicion.hide()
        self.carrito_manager.desbloquear_edicion()

    def cargar_datos_para_edicion(self):
        try:
            query = "SELECT v.id_cotizacion, c.nombre_completo, v.fecha, TO_CHAR(v.hora, 'HH24:MI'), v.total FROM cotizaciones v JOIN clientes c ON v.id_cliente = c.id_cliente WHERE v.folio = %s"
            res = self.db.fetch_one(query, (self.folio_editar,))
            if res:
                self.id_cot_actual, cliente, fecha, hora, total = res
                self.input_cliente.setText(cliente)
                

                query_det = """
                    SELECT p.id_producto, p.codigo, p.nombre, p.unidad_medida, d.cantidad, d.descuento, d.precio_unitario, d.subtotal 
                    FROM detalle_cotizacion d 
                    JOIN productos p ON d.id_producto = p.id_producto 
                    WHERE d.id_cotizacion = %s
                """
                detalles_db = self.db.fetch_all(query_det, (self.id_cot_actual,))
                
                carrito_lista = []
                for d in detalles_db:
                    carrito_lista.append({ 
                        "id": d[0], "codigo": d[1], "nombre": d[2], "unidad": d[3], 
                        "cant": float(d[4]), "desc": float(d[5]), 
                        "precio": float(d[6]), "subtotal": float(d[7]) 
                    })
                
                self.carrito_manager.cargar_carrito_existente(carrito_lista)
                self.bloquear_interfaz()
                self.btn_habilitar_edicion.show()
                self.btn_convertir.show()
        except Exception as e:
            pass

    def save_quotation(self):
        productos, total = self.carrito_manager.obtener_datos()
        if not productos:
            AlertaCustom.show_error(self, "Carrito Vacío", "No hay artículos para cotizar.")
            return

        try:
            now = datetime.datetime.now()
            hora_limpia = now.strftime('%H:%M')

            if self.folio_editar and self.modo_edicion_activo:
                self.db.execute_query("UPDATE cotizaciones SET total = %s, hora = %s WHERE id_cotizacion = %s", (total, hora_limpia, self.id_cot_actual))
                self.db.execute_query("DELETE FROM detalle_cotizacion WHERE id_cotizacion = %s", (self.id_cot_actual,))
                id_final = self.id_cot_actual
                folio_final = self.folio_editar
            else:
                folio_final = f"COT-{now.strftime('%Y%m%d%H%M%S')}"
                query_ins = "INSERT INTO cotizaciones (folio, id_vendedor, fecha, hora, id_cliente, total) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_cotizacion"
                id_final = self.db.fetch_one(query_ins, (folio_final, self.user_data['id'], now.date(), hora_limpia, 1, total))[0]

            query_det = "INSERT INTO detalle_cotizacion (id_cotizacion, id_producto, cantidad, precio_unitario, descuento, subtotal) VALUES (%s, %s, %s, %s, %s, %s)"
            for p in productos:
                self.db.execute_query(query_det, (id_final, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

            self.ws_cliente.sendTextMessage(json.dumps({"tipo": "NUEVA_COTIZACION", "folio": folio_final}))
            AlertaCustom.show_success(self, "Éxito", f"Cotización {folio_final} guardada correctamente.")
            self.accept()
        except Exception as e:
            AlertaCustom.show_error(self, "Error al Guardar", str(e))

    def convertir_a_venta(self):
        if AlertaCustom.ask_confirm(self, "Convertir a Venta", "¿Deseas generar una Orden de Venta con estos productos?"):
            try:
                productos, total = self.carrito_manager.obtener_datos()
                now = datetime.datetime.now()
                folio_ov = f"OV-{now.strftime('%Y%m%d%H%M%S')}"
                
                query_ov = "INSERT INTO orden_venta (folio, id_vendedor, fecha, hora, id_cliente, total, estatus) VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente') RETURNING id_venta"
                id_v = self.db.fetch_one(query_ov, (folio_ov, self.user_data['id'], now.date(), now.strftime('%H:%M'), 1, total))[0]
                
                query_dv = "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento, subtotal) VALUES (%s, %s, %s, %s, %s, %s)"
                for p in productos:
                    self.db.execute_query(query_dv, (id_v, p['id'], p['cant'], p['precio'], p['desc'], p['subtotal']))

                self.ws_cliente.sendTextMessage(json.dumps({"tipo": "NUEVA_ORDEN", "folio": folio_ov}))
                AlertaCustom.show_success(self, "Venta Generada", f"Se creó la orden {folio_ov}. El cajero ya puede cobrarla.")
                self.accept()
            except Exception as e:
                AlertaCustom.show_error(self, "Error de Conversión", str(e))

    def procesar_busqueda(self):
        texto = self.search_input.text().strip()
        if not texto: return
        if texto.isdigit():
            self.agregar_por_codigo_directo(texto)
        else:
            self.abrir_buscador_avanzado(texto)
        self.search_input.clear()

    def agregar_por_codigo_directo(self, codigo):
        
        query = "SELECT id_producto, codigo, nombre, unidad_medida, precio_venta FROM productos WHERE codigo = %s AND estatus = TRUE"
        p = self.db.fetch_one(query, (codigo,))
        if p:
            self.carrito_manager.agregar_producto(p[0], p[1], p[2], p[3], p[4])
        else:
            AlertaCustom.show_error(self, "No Encontrado", f"El código {codigo} no existe.")

    def abrir_buscador_avanzado(self, texto):
        def query_func(t):
            
            return self.db.fetch_all("SELECT codigo, nombre, unidad_medida, precio_venta, id_producto FROM productos WHERE estatus=TRUE AND (codigo ILIKE %s OR nombre ILIKE %s) LIMIT 50", (f"%{t}%", f"%{t}%"))

        modal = GenericSearchModal("Buscar Producto", "Escribe para buscar...", ["CODIGO", "NOMBRE", "UNIDAD", "PRECIO", "ID"], query_func, self)
        if texto: modal.search_input.setText(texto)
        if modal.exec():
            self.agregar_por_codigo_directo(modal.selected_data[0])

    def keyPressEvent(self, event):
    
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
        else:
            super().keyPressEvent(event)



class VisorCotizacionModal(QDialog):
    """Ventana para previsualizar el PDF renderizado y las opciones de envío"""
    def __init__(self, ruta_pdf, datos, parent=None):
        super().__init__(parent)
        self.ruta_pdf = ruta_pdf
        self.datos = datos
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Cotización: {self.datos['folio']}")
        
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setStyleSheet("background-color: white;")
        
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        panel_pdf = QVBoxLayout()
        lbl_preview_title = QLabel("📄 VISTA PREVIA DEL DOCUMENTO")
        lbl_preview_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #475569;")
        panel_pdf.addWidget(lbl_preview_title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: 1px solid #cbd5e1; background-color: #cbd5e1;")
        
        self.lbl_pdf_image = QLabel("Cargando vista previa...")
        self.lbl_pdf_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.lbl_pdf_image)
        panel_pdf.addWidget(self.scroll_area)
        
        main_layout.addLayout(panel_pdf, stretch=6)

        
        panel_controles = QVBoxLayout()
        panel_controles.setSpacing(15)

        lbl_titulo = QLabel("✅ ¡Generada con Éxito!")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #10b981;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_controles.addWidget(lbl_titulo)

        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("background-color: #f8fafc; border-radius: 8px; border: 1px solid #cbd5e1;")
        resumen_ly = QVBoxLayout(resumen_frame)
        
        lbl_info = QLabel(f"""
            <h3 style='color: #1e293b; margin-top:0;'>Resumen General</h3>
            <b>Folio:</b> {self.datos['folio']}<br>
            <b>Cliente:</b> {self.datos['cliente']}<br>
            <b>Vendedor:</b> {self.datos['vendedor']}<br>
            <b>Artículos:</b> {len(self.datos['productos'])}<br><br>
            <h2 style='color: #3b82f6; margin-bottom:0;'>TOTAL: ${self.datos['total']:,.2f}</h2>
        """)
        lbl_info.setStyleSheet("font-size: 15px; color: #475569;")
        resumen_ly.addWidget(lbl_info)
        panel_controles.addWidget(resumen_frame)

        lbl_ruta = QLabel(f"<b>Guardado localmente en:</b><br><span style='color: gray; font-size:11px;'>{self.ruta_pdf}</span>")
        lbl_ruta.setWordWrap(True)
        panel_controles.addWidget(lbl_ruta)

        panel_controles.addStretch()

        # Botones Principales
        btn_abrir = QPushButton("📂 ABRIR EN LECTOR PREDETERMINADO")
        btn_abrir.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_abrir.clicked.connect(self.abrir_archivo)

        btn_imprimir = QPushButton("🖨️ MANDAR A IMPRESORA")
        btn_imprimir.setStyleSheet("background-color: #64748b; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_imprimir.clicked.connect(self.simular_impresion)

        panel_controles.addWidget(btn_abrir)
        panel_controles.addWidget(btn_imprimir)

        # Formulario de Envío por Correo
        frame_correo = QFrame()
        frame_correo.setStyleSheet("background-color: #fffbeb; border: 1px solid #fcd34d; border-radius: 6px; padding: 5px;")
        ly_correo = QVBoxLayout(frame_correo)
        
        lbl_correo = QLabel("<b>Enviar archivo al cliente por correo:</b>")
        lbl_correo.setStyleSheet("color: #92400e; font-size: 12px;")
        ly_correo.addWidget(lbl_correo)

        input_ly = QHBoxLayout()
        self.input_correo = QLineEdit()
        self.input_correo.setPlaceholderText("cliente@correo.com")
        self.input_correo.setStyleSheet("padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; background-color: white;")
        
        btn_correo = QPushButton("📧 ENVIAR")
        btn_correo.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_correo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_correo.clicked.connect(self.simular_correo)
        
        input_ly.addWidget(self.input_correo)
        input_ly.addWidget(btn_correo)
        ly_correo.addLayout(input_ly)
        
        panel_controles.addWidget(frame_correo)
        
        main_layout.addLayout(panel_controles, stretch=4)
        
        # Iniciar Renderizado
        self.renderizar_pdf_hd()

    def renderizar_pdf_hd(self):
        try:
            doc = fitz.open(self.ruta_pdf)
            page = doc.load_page(0) 
            
            # El zoom dicta la calidad HD de la imagen resultante
            zoom = 1.8 
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            
            self.lbl_pdf_image.setPixmap(QPixmap.fromImage(img))
            
        except Exception as e:
            self.lbl_pdf_image.setText(f"No se pudo cargar la vista previa:\n{e}")

    def abrir_archivo(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.ruta_pdf)
            else:
                import subprocess
                subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", self.ruta_pdf])
        except Exception as e:
            AlertaCustom.show_error(self, "Error", f"No se pudo abrir el archivo: {e}")

    def simular_impresion(self):
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        from frontend.components.alertas import AlertaCustom
        
        try:
            # 1. Creamos el objeto del sistema de impresión
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # 2. Abrimos la ventana nativa de impresión de Windows
            dialogo_impresion = QPrintDialog(printer, self)
            
            if dialogo_impresion.exec() == QPrintDialog.DialogCode.Accepted:
                # Si el usuario selecciona una impresora y le da a "Imprimir"
                impresora_nombre = printer.printerName()
                AlertaCustom.show_success(
                    self, 
                    "Enviado a Impresora", 
                    f"La cotización {self.datos['folio']} se envió con éxito a:\n{impresora_nombre}"
                )
            else:
                # Si el usuario cancela el diálogo de Windows
                print("Impresión cancelada por el usuario.")
                
        except Exception as e:
            # Respaldo por si la computadora no tiene el servicio de impresión de Windows activo
            from PyQt6.QtWidgets import QInputDialog
            impresoras = ["Microsoft Print to PDF", "Impresora Genérica EPSON"]
            impresora, ok = QInputDialog.getItem(self, "Imprimir Cotización", "Selecciona impresora:", impresoras, 0, False)
            if ok and impresora:
                AlertaCustom.show_info(self, "Imprimiendo", f"Enviando a: {impresora}")
            
    def simular_correo(self):
        correo = self.input_correo.text().strip()
        if not correo:
            AlertaCustom.show_error(self, "Falta Correo", "Por favor ingresa la dirección de correo electrónico del cliente.")
            return
            
        AlertaCustom.show_success(self, "Correo Enviado", f"El archivo PDF se ha enviado con éxito a:\n{correo}")
        self.input_correo.clear()