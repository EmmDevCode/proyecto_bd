# backend/generador_pdf.py
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors

class GeneradorPDF:
    def __init__(self):
        self.color_primario = colors.HexColor("#3b82f6") # Blue-500
        self.color_secundario = colors.HexColor("#0f172a") # Slate-900
        self.color_gris_claro = colors.HexColor("#f8fafc") # Slate-50
        self.color_gris_borde = colors.HexColor("#e2e8f0") # Slate-200
        self.color_texto = colors.HexColor("#334155") # Slate-700
        
        self.styles = getSampleStyleSheet()
        self.estilo_titulo = ParagraphStyle(
            'Titulo', parent=self.styles['Heading1'], fontSize=22, 
            textColor=self.color_secundario, spaceAfter=5, fontName='Helvetica-Bold'
        )
        self.estilo_subtitulo = ParagraphStyle(
            'Subtitulo', parent=self.styles['Normal'], fontSize=11, 
            textColor=colors.gray, spaceAfter=15, fontName='Helvetica'
        )
        self.estilo_normal = ParagraphStyle(
            'NormalCustom', parent=self.styles['Normal'], fontSize=10, 
            textColor=self.color_texto, leading=14, fontName='Helvetica'
        )
        self.estilo_celda = ParagraphStyle(
            'Celda', parent=self.styles['Normal'], fontSize=9, leading=12, textColor=self.color_texto
        )

    def generar_cotizacion(self, datos_cotizacion, ruta_salida):
        doc = SimpleDocTemplate(ruta_salida, pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elementos = []

        # 1. ENCABEZADO
        directorio_base = os.getcwd()
        ruta_logo = os.path.join(directorio_base, "frontend", "assets", "logo.png")
        
        logo = None
        if os.path.exists(ruta_logo):
            logo = Image(ruta_logo, width=2.5*inch, height=1.5*inch)
            logo.preserveAspectRatio = True

        info_empresa = Paragraph("""
            <font size=14 color='#0f172a'><b>EL TORNILLO FELIZ</b></font><br/>
            <font color='#64748b'>Tu Ferretería, Siempre Contigo</font><br/>
            Calle 25 #123, Colonia Centro<br/>
            Tel: (999) 123-4567<br/>
            contacto@eltornillofeliz.com
        """, self.estilo_normal)

        tabla_encabezado = Table([[logo, info_empresa]], colWidths=[3*inch, 4*inch])
        tabla_encabezado.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabla_encabezado)
        
        # Línea separadora
        linea = Table([['']], colWidths=[7*inch])
        linea.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 1, self.color_gris_borde)]))
        elementos.append(linea)
        elementos.append(Spacer(1, 15))

        # 2. TÍTULO Y DATOS DEL CLIENTE
        elementos.append(Paragraph("COTIZACIÓN", self.estilo_titulo))
        elementos.append(Paragraph(f"Folio: {datos_cotizacion.get('folio', 'S/N')}", self.estilo_subtitulo))
        
        fecha_texto = datetime.strptime(datos_cotizacion.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if datos_cotizacion.get('fecha') else 'N/A'
        
        # Tarjeta de Info del Cliente (Tabla con fondo)
        info_izq = Paragraph(f"<b>CLIENTE:</b><br/>{datos_cotizacion.get('cliente', 'Mostrador')}<br/><br/><b>ATENDIDO POR:</b><br/>{datos_cotizacion.get('vendedor', 'Vendedor')}", self.estilo_normal)
        info_der = Paragraph(f"<b>FECHA DE EMISIÓN:</b><br/>{fecha_texto}<br/><br/><b>VIGENCIA:</b><br/>15 días", self.estilo_normal)
        
        tabla_cliente = Table([[info_izq, info_der]], colWidths=[4*inch, 3*inch])
        tabla_cliente.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.color_gris_claro),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1, self.color_gris_borde),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elementos.append(tabla_cliente)
        elementos.append(Spacer(1, 25))

        # 3. TABLA DE PRODUCTOS (Calculando precios SIN IVA)
        datos_tabla = [['Código', 'Descripción', 'Cant.', 'Desc %', 'Precio U.', 'Importe']]
        
        subtotal_general = 0.0 # Acumulador del precio real sin IVA
        
        for prod in datos_cotizacion.get('productos', []):
            desc_formateada = Paragraph(str(prod[1]), self.estilo_celda)
            
            # prod[4] es precio unitario y prod[5] es subtotal (Ambos traen IVA desde la BD)
            precio_con_iva = float(prod[4])
            importe_con_iva = float(prod[5])
            
            # Desglosamos el IVA (Dividimos entre 1.16)
            precio_sin_iva = precio_con_iva / 1.16
            importe_sin_iva = importe_con_iva / 1.16
            
            subtotal_general += importe_sin_iva
            
            fila = [
                str(prod[0]), 
                desc_formateada, 
                str(prod[2]), 
                f"{prod[3]}%", 
                f"${precio_sin_iva:,.2f}", 
                f"${importe_sin_iva:,.2f}"
            ]
            datos_tabla.append(fila)

        tabla_productos = Table(datos_tabla, colWidths=[1*inch, 2.5*inch, 0.7*inch, 0.8*inch, 1*inch, 1*inch])
        estilo_tabla = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.color_primario),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, self.color_gris_borde),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, self.color_gris_borde),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.color_texto),
        ])
        
        for i in range(1, len(datos_tabla)):
            if i % 2 == 0:
                estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f1f5f9"))
                
        tabla_productos.setStyle(estilo_tabla)
        elementos.append(tabla_productos)
        elementos.append(Spacer(1, 15))

        # 4. TOTALES (Subtotal, IVA, Total)
        total_final = float(datos_cotizacion.get('total', 0.0))
        monto_iva = total_final - subtotal_general
        
        tabla_totales = Table([
            ['SUBTOTAL:', f"${subtotal_general:,.2f}"],
            ['IVA (16%):', f"${monto_iva:,.2f}"],
            ['TOTAL A PAGAR:', f"${total_final:,.2f}"]
        ], colWidths=[5.5*inch, 1.5*inch])
        
        tabla_totales.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (1, 1), 'Helvetica'),
            ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTSIZE', (0, 2), (1, 2), 14),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.color_secundario),
            ('TEXTCOLOR', (0, 2), (1, 2), self.color_primario),
            ('LINEABOVE', (0, 2), (1, 2), 1.5, self.color_gris_borde),
            ('TOPPADDING', (0, 2), (1, 2), 8),
            ('BOTTOMPADDING', (0, 2), (1, 2), 8),
        ]))
        elementos.append(tabla_totales)
        elementos.append(Spacer(1, 40))

        # 5. PIE DE PÁGINA
        pie_pagina = Paragraph(
            "<font color='#64748b'><i>Precios sujetos a cambios sin previo aviso. Esta cotización no representa una reserva de inventario.</i></font><br/><br/>"
            "<font color='#0f172a'><b>¡Gracias por tu preferencia!</b></font>", 
            ParagraphStyle('Pie', parent=self.estilo_normal, alignment=1) 
        )
        elementos.append(pie_pagina)

        doc.build(elementos)
        return True

    def generar_ticket_venta(self, datos_venta, ruta_salida):
        """
        Genera un PDF con formato de rollo térmico (80mm) con Logo y Ahorro.
        """
        ancho_ticket = 80 * mm
        alto_ticket = 250 * mm 
        
        doc = SimpleDocTemplate(
            ruta_salida, 
            pagesize=(ancho_ticket, alto_ticket),
            rightMargin=3*mm, leftMargin=3*mm, 
            topMargin=5*mm, bottomMargin=5*mm
        )
        elementos = []

        estilo_centro = ParagraphStyle('Centro', parent=self.styles['Normal'], alignment=1, fontSize=8, leading=10, fontName='Helvetica')
        estilo_izq = ParagraphStyle('Izq', parent=self.styles['Normal'], alignment=0, fontSize=8, leading=11, fontName='Helvetica')
        estilo_prod = ParagraphStyle('Prod', parent=self.styles['Normal'], alignment=0, fontSize=7.5, leading=9, fontName='Helvetica')
        
        # 1. ENCABEZADO Y LOGO
        directorio_base = os.getcwd()
        ruta_logo = os.path.join(directorio_base, "frontend", "assets", "logo.png")
        if os.path.exists(ruta_logo):
            logo = Image(ruta_logo, width=35*mm, height=18*mm)
            logo.preserveAspectRatio = True
            logo.hAlign = 'CENTER'
            elementos.append(logo)
            elementos.append(Spacer(1, 2*mm))

        elementos.append(Paragraph("<b>EL TORNILLO FELIZ</b>", ParagraphStyle('TituloTicket', parent=estilo_centro, fontSize=13, fontName='Helvetica-Bold')))
        elementos.append(Paragraph("Tu Ferretería, Siempre Contigo", estilo_centro))
        elementos.append(Paragraph("Calle 25 #123, Colonia Centro<br/>Tel: (999) 123-4567", estilo_centro))
        
        # Usamos tablas para generar líneas sólidas en vez de guiones
        def draw_line():
            line = Table([['']], colWidths=[74*mm])
            line.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#334155"))]))
            return line

        elementos.append(Spacer(1, 2*mm))
        elementos.append(draw_line())
        elementos.append(Spacer(1, 2*mm))
        
        # 2. DATOS DE LA VENTA
        fecha_texto = datetime.strptime(datos_venta.get('fecha', ''), '%Y-%m-%d').strftime('%d/%m/%Y') if datos_venta.get('fecha') else 'N/A'
        hora = datos_venta.get('hora', '00:00')
        
        info_venta = f"""
        <b>Ticket:</b> #{datos_venta.get('folio', 'S/N')}<br/>
        <b>Fecha:</b> {fecha_texto} {hora}<br/>
        <b>Cajero:</b> {datos_venta.get('cajero', 'Caja 1')}<br/>
        <b>Cliente:</b> {datos_venta.get('cliente', 'Mostrador')}
        """
        elementos.append(Paragraph(info_venta, estilo_izq))
        elementos.append(Spacer(1, 2*mm))
        elementos.append(draw_line())
        elementos.append(Spacer(1, 2*mm))

        # 3. TABLA DE PRODUCTOS Y CÁLCULO DE AHORRO
        datos_tabla = [['CANT', 'DESCRIPCIÓN', 'IMPORTE']]
        ahorro_total = 0.0
        
        for prod in datos_venta.get('productos', []):
            cant = float(prod[2])
            desc = Paragraph(str(prod[1]), estilo_prod)
            precio_unitario = float(prod[4])
            importe_final = float(prod[5])
            
            # Calculamos si hubo descuento restando el total real vs el importe pagado
            subtotal_base = cant * precio_unitario
            if subtotal_base > importe_final:
                ahorro_total += (subtotal_base - importe_final)
            
            datos_tabla.append([str(int(cant)), desc, f"${importe_final:,.2f}"])

        tabla_productos = Table(datos_tabla, colWidths=[9*mm, 45*mm, 20*mm])
        tabla_productos.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#94a3b8")), 
        ]))
        elementos.append(tabla_productos)
        elementos.append(Spacer(1, 2*mm))
        elementos.append(draw_line())
        elementos.append(Spacer(1, 2*mm))

        # 4. TOTALES (Con USTED AHORRA dinámico)
        total_final = float(datos_venta.get('total', 0.0))
        recibido = float(datos_venta.get('recibido', 0.0))
        cambio = float(datos_venta.get('cambio', 0.0))
        metodo = datos_venta.get('metodo', 'Efectivo')

        filas_totales = []
        if ahorro_total > 0:
            subtotal_original = total_final + ahorro_total
            filas_totales.append(['SUBTOTAL:', f"${subtotal_original:,.2f}"])
            filas_totales.append(['AHORRO:', f"-${ahorro_total:,.2f}"])
        
        filas_totales.append(['TOTAL:', f"${total_final:,.2f}"])
        filas_totales.append(['', ''])
        filas_totales.append([f'PAGO ({metodo}):', f"${recibido:,.2f}"])
        filas_totales.append(['CAMBIO:', f"${cambio:,.2f}"])

        tabla_totales = Table(filas_totales, colWidths=[44*mm, 30*mm])
        
        estilo_totales = TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
        ])
        
        # Aplicamos negrita al total
        idx_total = len(filas_totales) - 4
        estilo_totales.add('FONTNAME', (0, idx_total), (-1, idx_total), 'Helvetica-Bold')
        estilo_totales.add('FONTSIZE', (0, idx_total), (-1, idx_total), 10)
        
        # Subrayado al total
        estilo_totales.add('LINEABOVE', (0, idx_total), (-1, idx_total), 0.5, colors.HexColor("#334155"))
        
        # Negrita al cambio
        estilo_totales.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        
        tabla_totales.setStyle(estilo_totales)
        elementos.append(tabla_totales)
        
        elementos.append(Spacer(1, 6*mm))
        elementos.append(Paragraph("<b>¡GRACIAS POR SU COMPRA!</b>", estilo_centro))
        elementos.append(Paragraph("Vuelva pronto", estilo_centro))

        doc.build(elementos)
        return True