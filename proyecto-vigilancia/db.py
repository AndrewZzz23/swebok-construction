"""Base de datos SQLite de VigiControl: esquema y datos de ejemplo."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash

RUTA_BD = Path(__file__).with_name("vigicontrol.db")

ESQUEMA = """
CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    usuario TEXT NOT NULL UNIQUE,
    clave_hash TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('supervisor','vigilante','tecnico')),
    celular TEXT,
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE puesto (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    cliente TEXT NOT NULL,
    direccion TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE turno (
    id INTEGER PRIMARY KEY,
    vigilante_id INTEGER NOT NULL REFERENCES usuario(id),
    puesto_id INTEGER NOT NULL REFERENCES puesto(id),
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL
);
CREATE TABLE marcacion (
    id INTEGER PRIMARY KEY,
    turno_id INTEGER NOT NULL REFERENCES turno(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('Llegada','Salida')),
    fecha TEXT NOT NULL,
    tarde INTEGER NOT NULL DEFAULT 0,
    UNIQUE (turno_id, tipo)
);
CREATE TABLE novedad (
    id INTEGER PRIMARY KEY,
    puesto_id INTEGER NOT NULL REFERENCES puesto(id),
    turno_id INTEGER REFERENCES turno(id),
    reportada_por INTEGER NOT NULL REFERENCES usuario(id),
    fecha TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Seguridad','Técnica','Otra')),
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Registrada',
    tecnico_id INTEGER REFERENCES usuario(id),
    llegada_tecnico TEXT,
    cerrada_en TEXT,
    solucion TEXT
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
    ahora = datetime.now().replace(second=0, microsecond=0)
    ins = con.execute

    usuarios = [
        ("Diana Torres", "supervisor", "supervisor123", "supervisor", "3001112233"),
        ("Juan Pérez", "juan", "vigilante123", "vigilante", "3002223344"),
        ("María López", "maria", "vigilante123", "vigilante", "3003334455"),
        ("Andrés Castro", "andres", "vigilante123", "vigilante", "3004445566"),
        ("Carlos Rojas", "carlos", "tecnico123", "tecnico", "3005556677"),
        ("Laura Méndez", "laura", "tecnico123", "tecnico", "3006667788"),
    ]
    for nombre, usuario, clave, rol, celular in usuarios:
        ins("INSERT INTO usuario (nombre, usuario, clave_hash, rol, celular) VALUES (?,?,?,?,?)",
            (nombre, usuario, generate_password_hash(clave), rol, celular))

    puestos = [
        ("Portería principal", "Conjunto Residencial Los Ocobos", "Cll 60 # 5-10, Ibagué"),
        ("Recepción", "Clínica San Rafael", "Cra 3 # 12-45, Ibagué"),
        ("Parqueadero", "Centro Comercial El Parque", "Av. Ambalá # 70-20, Ibagué"),
    ]
    for p in puestos:
        ins("INSERT INTO puesto (nombre, cliente, direccion) VALUES (?,?,?)", p)

    def turno(vigilante, puesto, inicio, horas=8):
        return ins("INSERT INTO turno (vigilante_id, puesto_id, inicio, fin) VALUES (?,?,?,?)",
                   (vigilante, puesto, hora(inicio), hora(inicio + timedelta(hours=horas)))).lastrowid

    def marcar(turno_id, tipo, fecha, tarde=0):
        ins("INSERT INTO marcacion (turno_id, tipo, fecha, tarde) VALUES (?,?,?,?)",
            (turno_id, tipo, hora(fecha), tarde))

    # Turnos de ayer, ya terminados.
    ayer = ahora - timedelta(days=1, hours=2)
    t1 = turno(2, 1, ayer)
    marcar(t1, "Llegada", ayer + timedelta(minutes=2))
    marcar(t1, "Salida", ayer + timedelta(hours=8, minutes=5))
    t2 = turno(3, 2, ayer)
    marcar(t2, "Llegada", ayer + timedelta(minutes=18), tarde=1)
    marcar(t2, "Salida", ayer + timedelta(hours=8))

    # Turnos de hoy.
    turno(2, 1, ahora - timedelta(minutes=5))                  # Juan: aún no marca llegada
    t4 = turno(3, 2, ahora - timedelta(hours=3))                # María: llegó tarde
    marcar(t4, "Llegada", ahora - timedelta(hours=2, minutes=35), tarde=1)
    turno(4, 3, ahora - timedelta(hours=1))                     # Andrés: no ha llegado
    turno(2, 1, ahora + timedelta(days=1))                      # Juan: mañana

    novedades = [
        (1, t1, 2, ayer + timedelta(hours=2), "Seguridad",
         "Persona sospechosa merodeando la portería. Se avisó al cuadrante de la Policía.", "Registrada",
         None, None, None, None),
        (1, t1, 2, ayer + timedelta(hours=5), "Técnica", "La cámara 2 de la entrada no graba.", "Cerrada",
         5, ayer + timedelta(hours=7), ayer + timedelta(hours=7, minutes=40), "Se cambió la fuente de poder."),
        (2, t4, 3, ahora - timedelta(hours=2), "Técnica", "La talanquera del parqueadero no abre.", "Asignada",
         6, None, None, None),
        (2, t4, 3, ahora - timedelta(hours=1), "Otra", "Se recibió un paquete para el área de facturación.",
         "Registrada", None, None, None, None),
    ]
    for (puesto, turno_id, autor, fecha, tipo, desc, estado, tecnico, llegada, cierre, solucion) in novedades:
        ins("INSERT INTO novedad (puesto_id, turno_id, reportada_por, fecha, tipo, descripcion, estado, "
            "tecnico_id, llegada_tecnico, cerrada_en, solucion) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (puesto, turno_id, autor, hora(fecha), tipo, desc, estado, tecnico,
             hora(llegada) if llegada else None, hora(cierre) if cierre else None, solucion))
    con.commit()
    con.close()


if __name__ == "__main__":
    crear_bd()
    print(f"Base de datos creada en {RUTA_BD}")
