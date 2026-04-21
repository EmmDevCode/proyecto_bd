-- ==========================================
-- 1. TABLAS INDEPENDIENTES (Catálogos base)
-- ==========================================
CREATE TABLE empleados (
    id_empleado SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(60) NOT NULL,
    usuario VARCHAR(30) UNIQUE NOT NULL,
    pin VARCHAR(4) NOT NULL,
    rol VARCHAR(20) NOT NULL,
    estatus BOOLEAN DEFAULT TRUE
);

CREATE TABLE clientes (
    id_cliente SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(60) NOT NULL,
    direccion VARCHAR(100),
    rfc VARCHAR(13) UNIQUE,
    telefono VARCHAR(10),
    correo VARCHAR(50),
    precio_mayoreo BOOLEAN DEFAULT FALSE,
    estatus BOOLEAN DEFAULT TRUE
);

CREATE TABLE proveedores (
    id_proveedor SERIAL PRIMARY KEY,
    nombre VARCHAR(60) NOT NULL,
    direccion VARCHAR(100),
    rfc VARCHAR(13) UNIQUE,
    telefono VARCHAR(10),
    correo VARCHAR(50),
    persona_contacto VARCHAR(60),
    estatus BOOLEAN DEFAULT TRUE
);

CREATE TABLE almacenes (
    id_almacen SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(45) NOT NULL,
    responsable VARCHAR(60),
    estatus BOOLEAN DEFAULT TRUE
);

-- ==========================================
-- 2. TABLAS DE PRIMER NIVEL DE DEPENDENCIA
-- ==========================================
CREATE TABLE productos (
    id_producto SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(60) NOT NULL,
    precio_compra DECIMAL(10,2) NOT NULL,
    precio_venta DECIMAL(10,2) NOT NULL,
    precio_mayoreo DECIMAL(10,2),
    impuesto DECIMAL(4,2),
    unidad_medida VARCHAR(15),
    id_proveedor INT REFERENCES proveedores(id_proveedor) ON DELETE RESTRICT,
    estatus BOOLEAN DEFAULT TRUE
);

CREATE TABLE cortes_caja (
    id_corte SERIAL PRIMARY KEY,
    id_cajero INT REFERENCES empleados(id_empleado) ON DELETE RESTRICT,
    fecha_hora_apertura TIMESTAMP NOT NULL,
    fecha_hora_cierre TIMESTAMP,
    fondo_inicial DECIMAL(10,2) NOT NULL,
    efectivo_fisico DECIMAL(10,2),
    total_sistema DECIMAL(10,2),
    diferencia DECIMAL(10,2),
    estatus VARCHAR(15)
);

-- ==========================================
-- 3. TABLAS TRANSACCIONALES (Cabeceras)
-- ==========================================
CREATE TABLE compras (
    id_compra SERIAL PRIMARY KEY,
    folio_interno VARCHAR(12) UNIQUE NOT NULL,
    id_proveedor INT REFERENCES proveedores(id_proveedor) ON DELETE RESTRICT,
    id_almacen_destino INT REFERENCES almacenes(id_almacen) ON DELETE RESTRICT,
    numero_factura VARCHAR(20),
    fecha DATE NOT NULL,
    tipo_cambio DECIMAL(6,2),
    impuestos_totales DECIMAL(10,2),
    total_compra DECIMAL(12,2) NOT NULL
);

CREATE TABLE orden_venta (
    id_venta SERIAL PRIMARY KEY,
    folio VARCHAR(12) UNIQUE NOT NULL,
    id_vendedor INT REFERENCES empleados(id_empleado) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    id_cliente INT REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    total DECIMAL(12,2) NOT NULL,
    estatus VARCHAR(15) NOT NULL DEFAULT 'Pendiente'
);

CREATE TABLE cotizaciones (
    id_cotizacion SERIAL PRIMARY KEY,
    folio VARCHAR(12) UNIQUE NOT NULL,
    id_vendedor INT REFERENCES empleados(id_empleado) ON DELETE RESTRICT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    id_cliente INT REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    total DECIMAL(12,2) NOT NULL
);

-- ==========================================
-- 4. TABLAS DE DETALLE (Partidas)
-- ==========================================
CREATE TABLE inventario_almacen (
    id_inventario SERIAL PRIMARY KEY,
    id_almacen INT REFERENCES almacenes(id_almacen) ON DELETE CASCADE,
    id_producto INT REFERENCES productos(id_producto) ON DELETE CASCADE,
    cantidad_existente DECIMAL(10,3) NOT NULL DEFAULT 0,
    CONSTRAINT uq_almacen_producto UNIQUE (id_almacen, id_producto)
);

CREATE TABLE detalle_compra (
    id_detallecom SERIAL PRIMARY KEY,
    id_compra INT REFERENCES compras(id_compra) ON DELETE CASCADE,
    id_producto INT REFERENCES productos(id_producto) ON DELETE RESTRICT,
    cantidad DECIMAL(10,3) NOT NULL,
    precio_compra DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL
);

CREATE TABLE detalle_venta (
    id_detalleven SERIAL PRIMARY KEY,
    id_venta INT REFERENCES orden_venta(id_venta) ON DELETE CASCADE,
    id_producto INT REFERENCES productos(id_producto) ON DELETE RESTRICT,
    cantidad DECIMAL(10,3) NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    descuento DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(12,2) NOT NULL
);

CREATE TABLE detalle_cotizacion (
    id_detallecot SERIAL PRIMARY KEY,
    id_cotizacion INT REFERENCES cotizaciones(id_cotizacion) ON DELETE CASCADE,
    id_producto INT REFERENCES productos(id_producto) ON DELETE RESTRICT,
    cantidad DECIMAL(10,3) NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    descuento DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(12,2) NOT NULL
);

-- ==========================================
-- 5. MÓDULO CAJA (Finalización de Venta)
-- ==========================================
CREATE TABLE cobro_venta (
    id_cobro SERIAL PRIMARY KEY,
    id_venta INT UNIQUE REFERENCES orden_venta(id_venta) ON DELETE RESTRICT,
    id_cajero INT REFERENCES empleados(id_empleado) ON DELETE RESTRICT,
    fecha_cobro TIMESTAMP NOT NULL,
    metodo_pago VARCHAR(20) NOT NULL,
    monto_recibido DECIMAL(12,2) NOT NULL,
    cambio DECIMAL(10,2) NOT NULL
);