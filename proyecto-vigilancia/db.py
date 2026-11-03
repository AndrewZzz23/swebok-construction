"""Base de datos SQLite de SIGEV: esquema y datos de ejemplo."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

RUTA_BD = Path(__file__).with_name("sigev.db")

ESQUEMA = """
CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    clave_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('admin','director','tecnico','almacenista')),
    tecnico_id INTEGER REFERENCES tecnico(id),
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE cliente (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    identificacion TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE cuenta (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    nombre TEXT NOT NULL,
    direccion TEXT NOT NULL,
    contacto TEXT,
    correo TEXT,
    ruta TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE capacidad (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE tecnico (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    documento TEXT NOT NULL,
    celular TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE tecnico_capacidad (
    tecnico_id INTEGER NOT NULL REFERENCES tecnico(id),
    capacidad_id INTEGER NOT NULL REFERENCES capacidad(id),
    PRIMARY KEY (tecnico_id, capacidad_id)
);
CREATE TABLE plantilla (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    prioridad INTEGER NOT NULL DEFAULT 2,
    tiempo_estimado INTEGER NOT NULL,
    capacidad_id INTEGER REFERENCES capacidad(id),
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE orden (
    id INTEGER PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuenta(id),
    plantilla_id INTEGER NOT NULL REFERENCES plantilla(id),
    prioridad INTEGER NOT NULL,
    estado TEXT NOT NULL DEFAULT 'En espera',
    comentarios TEXT,
    tecnico_id INTEGER REFERENCES tecnico(id),
    programada_para TEXT,
    creada_en TEXT NOT NULL,
    creada_por TEXT NOT NULL,
    inicio TEXT,
    fin TEXT,
    diagnostico TEXT,
    solucion TEXT
);
CREATE TABLE pausa (
    id INTEGER PRIMARY KEY,
    orden_id INTEGER NOT NULL REFERENCES orden(id),
    motivo TEXT NOT NULL,
    inicio TEXT NOT NULL,
    fin TEXT
);
CREATE TABLE orden_evento (
    id INTEGER PRIMARY KEY,
    orden_id INTEGER NOT NULL REFERENCES orden(id),
    fecha TEXT NOT NULL,
    usuario TEXT NOT NULL,
    tipo TEXT NOT NULL,
    detalle TEXT
);
CREATE TABLE articulo (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    unidad TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Recuperable','Consumible')),
    existencia_minima INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE bodega (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Principal','Cuenta')),
    cuenta_id INTEGER REFERENCES cuenta(id)
);
CREATE TABLE movimiento (
    id INTEGER PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('Entrada','Traslado')),
    fecha TEXT NOT NULL,
    articulo_id INTEGER NOT NULL REFERENCES articulo(id),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    bodega_origen_id INTEGER REFERENCES bodega(id),
    bodega_destino_id INTEGER NOT NULL REFERENCES bodega(id),
    orden_id INTEGER REFERENCES orden(id),
    proveedor TEXT,
    factura TEXT,
    usuario TEXT NOT NULL
);
CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL,
    usuario TEXT NOT NULL,
    modulo TEXT NOT NULL,
    accion TEXT NOT NULL,
    registro TEXT,
    detalle TEXT
);
"""


def conectar():
    con = sqlite3.connect(RUTA_BD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def hora(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def crear_bd():
    """Crea la base de datos desde cero con datos de ejemplo."""
    if RUTA_BD.exists():
        RUTA_BD.unlink()
    con = conectar()
    con.executescript(ESQUEMA)
    ahora = datetime.now().replace(microsecond=0)
    ins = con.execute

    for nombre in ("CCTV", "Alarmas", "Control de acceso", "Cercas eléctricas"):
        ins("INSERT INTO capacidad (nombre) VALUES (?)", (nombre,))

    tecnicos = [
        ("Carlos Rojas", "1110456789", "3001234567", (1, 2)),
        ("Laura Méndez", "1110987654", "3017654321", (2, 3)),
        ("Pedro Gómez", "93456123", "3159876543", (1, 4)),
    ]
    for nombre, doc, cel, caps in tecnicos:
        tid = ins("INSERT INTO tecnico (nombre, documento, celular) VALUES (?,?,?)",
                  (nombre, doc, cel)).lastrowid
        for c in caps:
            ins("INSERT INTO tecnico_capacidad VALUES (?,?)", (tid, c))

    usuarios = [
        ("Administrador", "admin", "admin123", "admin", None),
        ("Diana Torres (Directora técnica)", "director", "director123", "director", None),
        ("Carlos Rojas", "carlos", "tecnico123", "tecnico", 1),
        ("Laura Méndez", "laura", "tecnico123", "tecnico", 2),
        ("Jorge Díaz (Almacenista)", "almacen", "almacen123", "almacenista", None),
    ]
    for nombre, usuario, clave, rol, tid in usuarios:
        ins("INSERT INTO usuario (nombre, usuario, clave_hash, rol, tecnico_id) VALUES (?,?,?,?,?)",
            (nombre, usuario, generate_password_hash(clave), rol, tid))

    clientes = [
        ("Clínica San Rafael", "900123456-1"),
        ("Conjunto Residencial Los Ocobos", "900654321-7"),
        ("Supermercados El Ahorro", "800987123-4"),
    ]
    for nombre, nit in clientes:
        ins("INSERT INTO cliente (nombre, identificacion) VALUES (?,?)", (nombre, nit))

    ins("INSERT INTO bodega (nombre, tipo) VALUES ('Bodega principal','Principal')")
    cuentas = [
        (1, "Sede Centro", "Cra 3 # 12-45, Ibagué", "Marta Ruiz", "seguridad@clinicasr.co", "Centro"),
        (1, "Sede El Vergel", "Cll 145 # 8-20, Ibagué", "Andrés Peña", "vergel@clinicasr.co", "Oriente"),
        (2, "Portería principal", "Cll 60 # 5-10, Ibagué", "Administración", "admin@losocobos.co", "Norte"),
        (3, "Punto Jordán", "Cra 5 # 70-12, Ibagué", "Luis Cárdenas", "jordan@elahorro.co", "Norte"),
        (3, "Punto Salado", "Cll 20 # 4-33, Ibagué", "Sandra Vela", "salado@elahorro.co", "Sur"),
    ]
    for cuenta in cuentas:
        cid = ins("INSERT INTO cuenta (cliente_id, nombre, direccion, contacto, correo, ruta) "
                  "VALUES (?,?,?,?,?,?)", cuenta).lastrowid
        ins("INSERT INTO bodega (nombre, tipo, cuenta_id) VALUES (?,?,?)",
            (f"Bodega {cuenta[1]}", "Cuenta", cid))

    plantillas = [
        ("Revisión de alarma disparada", "Verificar sensores y panel tras un disparo.", 1, 45, 2),
        ("Mantenimiento preventivo CCTV", "Limpieza, enfoque y revisión de grabación.", 2, 90, 1),
        ("Instalación de cámara", "Instalar y configurar una cámara nueva.", 2, 120, 1),
        ("Falla en control de acceso", "Lector o cerradura sin funcionar.", 1, 60, 3),
        ("Revisión de cerca eléctrica", "Medir voltaje y revisar aisladores.", 3, 60, 4),
    ]
    for p in plantillas:
        ins("INSERT INTO plantilla (nombre, descripcion, prioridad, tiempo_estimado, capacidad_id) "
            "VALUES (?,?,?,?,?)", p)

    articulos = [
        ("CAM-4MP", "Cámara domo 4MP", "Unidad", "Recuperable", 5, 12),
        ("PIR-01", "Sensor de movimiento PIR", "Unidad", "Recuperable", 10, 25),
        ("PAN-AL", "Panel de alarma 8 zonas", "Unidad", "Recuperable", 2, 3),
        ("UTP-6", "Cable UTP Cat 6", "Metro", "Consumible", 100, 305),
        ("CHZ-14", "Chazos 1/4 con tornillo", "Unidad", "Consumible", 200, 150),
    ]
    for codigo, nombre, unidad, tipo, minimo, cantidad in articulos:
        aid = ins("INSERT INTO articulo (codigo, nombre, unidad, tipo, existencia_minima) "
                  "VALUES (?,?,?,?,?)", (codigo, nombre, unidad, tipo, minimo)).lastrowid
        ins("INSERT INTO movimiento (tipo, fecha, articulo_id, cantidad, bodega_destino_id, "
            "proveedor, factura, usuario) VALUES ('Entrada',?,?,?,1,'Distribuidora SegTec','FV-2201','almacen')",
            (hora(ahora - timedelta(days=10)), aid, cantidad))

    def orden(cuenta, plantilla, estado, tecnico=None, programada=None, inicio=None, fin=None,
              diagnostico=None, solucion=None, comentarios=None, hace=1):
        prioridad = con.execute("SELECT prioridad FROM plantilla WHERE id=?", (plantilla,)).fetchone()[0]
        creada = hora(ahora - timedelta(days=hace))
        oid = ins("INSERT INTO orden (cuenta_id, plantilla_id, prioridad, estado, comentarios, tecnico_id, "
                  "programada_para, creada_en, creada_por, inicio, fin, diagnostico, solucion) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (cuenta, plantilla, prioridad, estado, comentarios, tecnico, programada, creada,
                   "director", inicio, fin, diagnostico, solucion)).lastrowid
        ins("INSERT INTO orden_evento (orden_id, fecha, usuario, tipo, detalle) VALUES (?,?,?,?,?)",
            (oid, creada, "director", "Creación", comentarios))
        if tecnico:
            nombre = con.execute("SELECT nombre FROM tecnico WHERE id=?", (tecnico,)).fetchone()[0]
            ins("INSERT INTO orden_evento (orden_id, fecha, usuario, tipo, detalle) VALUES (?,?,?,?,?)",
                (oid, creada, "director", "Asignación",
                 f"{nombre} para el {datetime.fromisoformat(programada):%d/%m/%Y %H:%M}"))
        tec_usuario = {1: "carlos", 2: "laura"}.get(tecnico, "tecnico")
        if inicio:
            ins("INSERT INTO orden_evento (orden_id, fecha, usuario, tipo, detalle) VALUES (?,?,?,?,?)",
                (oid, inicio, tec_usuario, "Inicio", None))
        if fin:
            ins("INSERT INTO orden_evento (orden_id, fecha, usuario, tipo, detalle) VALUES (?,?,?,?,?)",
                (oid, fin, tec_usuario, "Cierre", diagnostico))
        return oid

    hace2 = ahora - timedelta(days=2, hours=3)
    o1 = orden(1, 2, "Finalizada", 1, hora(hace2), hora(hace2), hora(hace2 + timedelta(minutes=105)),
               "Cámara 3 desenfocada y DVR con disco al 95%.", "Se enfocó la cámara y se liberó espacio.",
               "Mantenimiento mensual.", hace=3)
    ins("INSERT INTO pausa (orden_id, motivo, inicio, fin) VALUES (?,?,?,?)",
        (o1, "Esperando acceso al cuarto técnico", hora(hace2 + timedelta(minutes=30)),
         hora(hace2 + timedelta(minutes=40))))
    hace1 = ahora - timedelta(days=1, hours=5)
    orden(4, 1, "Finalizada", 2, hora(hace1), hora(hace1), hora(hace1 + timedelta(minutes=35)),
          "Sensor PIR de bodega con batería baja.", "Cambio de batería y prueba de zona.", hace=2)
    orden(3, 4, "En ejecución", 1, hora(ahora - timedelta(minutes=70)), hora(ahora - timedelta(minutes=65)),
          comentarios="El lector de la portería no reconoce tarjetas.")
    orden(2, 3, "Asignada", 3, hora(ahora + timedelta(days=1)), comentarios="Cámara nueva en parqueadero.")
    orden(5, 5, "En espera", comentarios="Cliente reporta chispas en un tramo.", hace=0)
    ins("INSERT INTO movimiento (tipo, fecha, articulo_id, cantidad, bodega_origen_id, bodega_destino_id, "
        "orden_id, usuario) VALUES ('Traslado',?,4,20,1,2,1,'almacen')", (hora(hace2),))

    ins("INSERT INTO auditoria (fecha, usuario, modulo, accion, registro, detalle) VALUES (?,?,?,?,?,?)",
        (hora(ahora), "sistema", "Sistema", "Carga inicial", None, "Datos de ejemplo"))
    con.commit()
    con.close()


if __name__ == "__main__":
    crear_bd()
    print(f"Base de datos creada en {RUTA_BD}")
