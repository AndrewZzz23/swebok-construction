"""SIGEV - Sistema de Gestión de Servicios de Vigilancia (prototipo).

Ejecutar:  python app.py   y abrir http://localhost:5000
"""
from datetime import datetime
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

import db

app = Flask(__name__)
app.secret_key = "sigev-prototipo-academico"

ROLES = {
    "admin": "Administrador",
    "director": "Director técnico",
    "tecnico": "Técnico",
    "almacenista": "Almacenista",
}
ESTADOS = ["En espera", "Asignada", "En ejecución", "Suspendida", "Finalizada", "Anulada"]
PRIORIDADES = {1: "Alta", 2: "Media", 3: "Baja"}
MOTIVOS_PAUSA = ["Esperando acceso al sitio", "Falta de material", "Almuerzo", "Solicitud del cliente", "Otro"]

# Catálogos con el mismo comportamiento: listar, crear, editar e inactivar.
# Cada campo: (columna, etiqueta, tipo, opciones)
CATALOGOS = {
    "clientes": {
        "titulo": "Clientes", "tabla": "cliente", "roles": ("admin", "director"),
        "campos": [("nombre", "Nombre", "texto", None), ("identificacion", "NIT / Cédula", "texto", None)],
    },
    "cuentas": {
        "titulo": "Cuentas (sedes)", "tabla": "cuenta", "roles": ("admin", "director"),
        "campos": [
            ("cliente_id", "Cliente", "fk", "cliente"),
            ("nombre", "Nombre de la sede", "texto", None),
            ("direccion", "Dirección", "texto", None),
            ("contacto", "Contacto", "texto", None),
            ("correo", "Correo del contacto", "correo", None),
            ("ruta", "Ruta", "lista", ["Centro", "Norte", "Sur", "Oriente", "Occidente"]),
        ],
    },
    "capacidades": {
        "titulo": "Capacidades técnicas", "tabla": "capacidad", "roles": ("admin", "director"),
        "campos": [("nombre", "Nombre", "texto", None)],
    },
    "tecnicos": {
        "titulo": "Técnicos", "tabla": "tecnico", "roles": ("admin", "director"),
        "campos": [
            ("nombre", "Nombre", "texto", None),
            ("documento", "Documento", "texto", None),
            ("celular", "Celular", "texto", None),
            ("capacidades", "Capacidades", "multiple", "capacidad"),
        ],
    },
    "plantillas": {
        "titulo": "Plantillas de servicio", "tabla": "plantilla", "roles": ("admin", "director"),
        "campos": [
            ("nombre", "Nombre", "texto", None),
            ("descripcion", "Descripción", "texto", None),
            ("prioridad", "Prioridad", "lista", PRIORIDADES),
            ("tiempo_estimado", "Tiempo estimado (min)", "numero", None),
            ("capacidad_id", "Capacidad requerida", "fk", "capacidad"),
        ],
    },
    "articulos": {
        "titulo": "Artículos de inventario", "tabla": "articulo", "roles": ("admin", "almacenista"),
        "campos": [
            ("codigo", "Código", "texto", None),
            ("nombre", "Nombre", "texto", None),
            ("unidad", "Unidad de medida", "lista", ["Unidad", "Metro", "Caja", "Rollo"]),
            ("tipo", "Tipo", "lista", ["Recuperable", "Consumible"]),
            ("existencia_minima", "Existencia mínima", "numero", None),
        ],
    },
}


# ---------------------------------------------------------------- utilidades

def bd():
    if "bd" not in g:
        g.bd = db.conectar()
    return g.bd


@app.teardown_appcontext
def cerrar_bd(_):
    con = g.pop("bd", None)
    if con is not None:
        con.close()


def ahora():
    return db.hora(datetime.now())


def minutos_entre(desde, hasta):
    a = datetime.fromisoformat(desde)
    b = datetime.fromisoformat(hasta)
    return max(0, round((b - a).total_seconds() / 60))


def auditar(modulo, accion, registro=None, detalle=None):
    """RF13: todo cambio queda registrado con usuario y fecha."""
    bd().execute(
        "INSERT INTO auditoria (fecha, usuario, modulo, accion, registro, detalle) VALUES (?,?,?,?,?,?)",
        (ahora(), g.usuario["usuario"] if g.get("usuario") else "anónimo", modulo, accion, registro, detalle),
    )


def evento(orden_id, tipo, detalle=None):
    bd().execute(
        "INSERT INTO orden_evento (orden_id, fecha, usuario, tipo, detalle) VALUES (?,?,?,?,?)",
        (orden_id, ahora(), g.usuario["usuario"], tipo, detalle),
    )


def requiere(*roles):
    """RF02: cada rol solo entra a lo que le corresponde."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not g.get("usuario"):
                return redirect(url_for("login", siguiente=request.path))
            if roles and g.usuario["rol"] not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


@app.before_request
def cargar_usuario():
    uid = session.get("uid")
    g.usuario = bd().execute("SELECT * FROM usuario WHERE id=? AND activo=1", (uid,)).fetchone() if uid else None


@app.context_processor
def globales():
    return {"ROLES": ROLES, "PRIORIDADES": PRIORIDADES, "CATALOGOS": CATALOGOS, "usuario": g.get("usuario")}


@app.template_filter("fecha")
def formato_fecha(valor):
    return datetime.fromisoformat(valor).strftime("%d/%m/%Y %H:%M") if valor else "—"


# ---------------------------------------------------------------- sesión (RF01)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = bd().execute("SELECT * FROM usuario WHERE usuario=? AND activo=1",
                         (request.form["usuario"].strip(),)).fetchone()
        if u and check_password_hash(u["clave_hash"], request.form["clave"]):
            session["uid"] = u["id"]
            g.usuario = u
            auditar("Sesión", "Inicio de sesión")
            bd().commit()
            return redirect(request.args.get("siguiente") or url_for("inicio"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    if g.usuario:
        auditar("Sesión", "Cierre de sesión")
        bd().commit()
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@requiere()
def inicio():
    if g.usuario["rol"] == "almacenista":
        return redirect(url_for("inventario"))
    return redirect(url_for("tablero"))


# ---------------------------------------------------------------- catálogos (RF03-RF06, RF11)

def opciones_fk(tabla):
    return bd().execute(f"SELECT id, nombre FROM {tabla} WHERE activo=1 ORDER BY nombre").fetchall()


def catalogo_o_404(nombre):
    cat = CATALOGOS.get(nombre) or abort(404)
    if g.usuario["rol"] not in cat["roles"]:
        abort(403)
    return cat


@app.route("/catalogos/<nombre>")
@requiere()
def catalogo_lista(nombre):
    cat = catalogo_o_404(nombre)
    filas = bd().execute(f"SELECT * FROM {cat['tabla']} ORDER BY activo DESC, id").fetchall()
    nombres = {}
    for col, _, tipo, origen in cat["campos"]:
        if tipo == "fk":
            nombres[col] = {r["id"]: r["nombre"] for r in bd().execute(f"SELECT id, nombre FROM {origen}")}
    capacidades = {}
    if nombre == "tecnicos":
        for r in bd().execute("SELECT tc.tecnico_id, c.nombre FROM tecnico_capacidad tc "
                              "JOIN capacidad c ON c.id = tc.capacidad_id"):
            capacidades.setdefault(r["tecnico_id"], []).append(r["nombre"])
    return render_template("catalogo_lista.html", nombre=nombre, cat=cat, filas=filas,
                           nombres=nombres, capacidades=capacidades)


@app.route("/catalogos/<nombre>/nuevo", methods=["GET", "POST"])
@app.route("/catalogos/<nombre>/<int:rid>", methods=["GET", "POST"])
@requiere()
def catalogo_form(nombre, rid=None):
    cat = catalogo_o_404(nombre)
    tabla = cat["tabla"]
    fila = bd().execute(f"SELECT * FROM {tabla} WHERE id=?", (rid,)).fetchone() if rid else None
    if rid and not fila:
        abort(404)
    seleccionadas = set()
    if nombre == "tecnicos" and rid:
        seleccionadas = {r[0] for r in bd().execute(
            "SELECT capacidad_id FROM tecnico_capacidad WHERE tecnico_id=?", (rid,))}

    if request.method == "POST":
        columnas = [c for c, _, tipo, _ in cat["campos"] if tipo != "multiple"]
        valores = [request.form.get(c, "").strip() or None for c in columnas]
        if any(v is None for c, v in zip(columnas, valores) if c in ("nombre", "codigo")):
            flash("El nombre es obligatorio.", "error")
        else:
            if rid:
                sets = ", ".join(f"{c}=?" for c in columnas)
                bd().execute(f"UPDATE {tabla} SET {sets} WHERE id=?", (*valores, rid))
                antes = {c: fila[c] for c in columnas}
                auditar(cat["titulo"], "Edición", f"{tabla} #{rid}", f"Antes: {antes}")
            else:
                marcas = ",".join("?" for _ in columnas)
                rid = bd().execute(f"INSERT INTO {tabla} ({','.join(columnas)}) VALUES ({marcas})",
                                   valores).lastrowid
                auditar(cat["titulo"], "Creación", f"{tabla} #{rid}", str(dict(zip(columnas, valores))))
                if tabla == "cuenta":
                    # Cada cuenta tiene su propia bodega para el material instalado.
                    bd().execute("INSERT INTO bodega (nombre, tipo, cuenta_id) VALUES (?,?,?)",
                                 (f"Bodega {request.form['nombre']}", "Cuenta", rid))
            if nombre == "tecnicos":
                bd().execute("DELETE FROM tecnico_capacidad WHERE tecnico_id=?", (rid,))
                for cap in request.form.getlist("capacidades"):
                    bd().execute("INSERT INTO tecnico_capacidad VALUES (?,?)", (rid, int(cap)))
            bd().commit()
            flash(f"{cat['titulo']}: registro guardado.", "ok")
            return redirect(url_for("catalogo_lista", nombre=nombre))

    opciones = {c: opciones_fk(o) for c, _, t, o in cat["campos"] if t in ("fk", "multiple")}
    return render_template("catalogo_form.html", nombre=nombre, cat=cat, fila=fila,
                           opciones=opciones, seleccionadas=seleccionadas)


@app.post("/catalogos/<nombre>/<int:rid>/estado")
@requiere()
def catalogo_estado(nombre, rid):
    """No se borra nada: los registros se inactivan o se vuelven a activar."""
    cat = catalogo_o_404(nombre)
    bd().execute(f"UPDATE {cat['tabla']} SET activo = 1 - activo WHERE id=?", (rid,))
    activo = bd().execute(f"SELECT activo FROM {cat['tabla']} WHERE id=?", (rid,)).fetchone()[0]
    auditar(cat["titulo"], "Activación" if activo else "Inactivación", f"{cat['tabla']} #{rid}")
    bd().commit()
    return redirect(url_for("catalogo_lista", nombre=nombre))


# ---------------------------------------------------------------- órdenes (RF07-RF10)

CONSULTA_ORDENES = """
SELECT o.*, c.nombre AS cuenta, c.direccion, c.contacto, c.correo, c.ruta, cl.nombre AS cliente,
       cl.id AS cliente_id, p.nombre AS plantilla, p.tiempo_estimado, p.capacidad_id,
       t.nombre AS tecnico
FROM orden o
JOIN cuenta c ON c.id = o.cuenta_id
JOIN cliente cl ON cl.id = c.cliente_id
JOIN plantilla p ON p.id = o.plantilla_id
LEFT JOIN tecnico t ON t.id = o.tecnico_id
"""


def tiempo_real(orden):
    """Minutos trabajados: desde el inicio hasta el cierre (o ahora), sin contar las pausas."""
    if not orden["inicio"]:
        return None
    fin = orden["fin"] or ahora()
    total = minutos_entre(orden["inicio"], fin)
    for p in bd().execute("SELECT * FROM pausa WHERE orden_id=?", (orden["id"],)):
        total -= minutos_entre(p["inicio"], p["fin"] or fin)
    return max(0, total)


def obtener_orden(oid):
    orden = bd().execute(CONSULTA_ORDENES + " WHERE o.id=?", (oid,)).fetchone()
    if not orden:
        abort(404)
    if g.usuario["rol"] == "tecnico" and orden["tecnico_id"] != g.usuario["tecnico_id"]:
        abort(403)
    return orden


@app.route("/ordenes")
@requiere("admin", "director", "tecnico")
def tablero():
    filtros, params = [], []
    if g.usuario["rol"] == "tecnico":
        filtros.append("o.tecnico_id=?")
        params.append(g.usuario["tecnico_id"])
    for campo, columna in (("estado", "o.estado"), ("tecnico", "o.tecnico_id"), ("cliente", "cl.id")):
        if request.args.get(campo):
            filtros.append(f"{columna}=?")
            params.append(request.args[campo])
    where = (" WHERE " + " AND ".join(filtros)) if filtros else ""
    ordenes = bd().execute(CONSULTA_ORDENES + where + " ORDER BY o.prioridad, o.creada_en", params).fetchall()
    tiempos = {o["id"]: tiempo_real(o) for o in ordenes}
    por_estado = {e: [o for o in ordenes if o["estado"] == e] for e in ESTADOS}
    return render_template("tablero.html", por_estado=por_estado, tiempos=tiempos, ESTADOS=ESTADOS,
                           tecnicos=opciones_fk("tecnico"), clientes=opciones_fk("cliente"))


@app.route("/ordenes/nueva", methods=["GET", "POST"])
@requiere("admin", "director")
def orden_nueva():
    if request.method == "POST":
        cuenta_id = int(request.form["cuenta_id"])
        plantilla_id = int(request.form["plantilla_id"])
        comentarios = request.form.get("comentarios", "").strip() or None
        # RF07: control de duplicados. Si ya hay una orden pendiente de la misma
        # cuenta y plantilla, no se crea otra: se agrega una nota y sube la prioridad.
        existente = bd().execute(
            "SELECT * FROM orden WHERE cuenta_id=? AND plantilla_id=? "
            "AND estado IN ('En espera','Asignada','Suspendida','En ejecución')",
            (cuenta_id, plantilla_id)).fetchone()
        if existente:
            nueva = max(1, existente["prioridad"] - 1)
            bd().execute("UPDATE orden SET prioridad=? WHERE id=?", (nueva, existente["id"]))
            evento(existente["id"], "Duplicado evitado",
                   f"Nueva solicitud: {comentarios or 'sin comentarios'}. Prioridad sube a {PRIORIDADES[nueva]}.")
            auditar("Órdenes", "Duplicado evitado", f"OT-{existente['id']:04d}")
            bd().commit()
            flash(f"Ya existía la orden OT-{existente['id']:04d} pendiente para esa cuenta y plantilla. "
                  "Se agregó la nota y se subió su prioridad.", "aviso")
            return redirect(url_for("orden_detalle", oid=existente["id"]))
        prioridad = bd().execute("SELECT prioridad FROM plantilla WHERE id=?", (plantilla_id,)).fetchone()[0]
        oid = bd().execute(
            "INSERT INTO orden (cuenta_id, plantilla_id, prioridad, comentarios, creada_en, creada_por) "
            "VALUES (?,?,?,?,?,?)",
            (cuenta_id, plantilla_id, prioridad, comentarios, ahora(), g.usuario["usuario"])).lastrowid
        evento(oid, "Creación", comentarios)
        auditar("Órdenes", "Creación", f"OT-{oid:04d}")
        bd().commit()
        flash(f"Orden OT-{oid:04d} creada.", "ok")
        return redirect(url_for("orden_detalle", oid=oid))
    cuentas = bd().execute("SELECT c.id, cl.nombre || ' — ' || c.nombre AS nombre FROM cuenta c "
                           "JOIN cliente cl ON cl.id=c.cliente_id WHERE c.activo=1 ORDER BY nombre").fetchall()
    return render_template("orden_nueva.html", cuentas=cuentas, plantillas=opciones_fk("plantilla"))


@app.route("/ordenes/<int:oid>")
@requiere("admin", "director", "tecnico", "almacenista")
def orden_detalle(oid):
    orden = obtener_orden(oid)
    eventos = bd().execute("SELECT * FROM orden_evento WHERE orden_id=? ORDER BY fecha, id", (oid,)).fetchall()
    pausas = bd().execute("SELECT * FROM pausa WHERE orden_id=? ORDER BY inicio", (oid,)).fetchall()
    material = bd().execute(
        "SELECT m.*, a.nombre, a.unidad, a.tipo FROM movimiento m JOIN articulo a ON a.id=m.articulo_id "
        "WHERE m.orden_id=? ORDER BY m.fecha", (oid,)).fetchall()
    # RF08: primero los técnicos que tienen la capacidad que pide la plantilla.
    tecnicos = bd().execute(
        "SELECT t.id, t.nombre, EXISTS(SELECT 1 FROM tecnico_capacidad tc WHERE tc.tecnico_id=t.id "
        "AND tc.capacidad_id=?) AS apto FROM tecnico t WHERE t.activo=1 ORDER BY apto DESC, t.nombre",
        (orden["capacidad_id"],)).fetchall()
    capacidad = bd().execute("SELECT nombre FROM capacidad WHERE id=?", (orden["capacidad_id"],)).fetchone()
    articulos = existencias_bodega(1)
    return render_template("orden_detalle.html", o=orden, eventos=eventos, pausas=pausas, material=material,
                           tecnicos=tecnicos, capacidad=capacidad["nombre"] if capacidad else "—",
                           real=tiempo_real(orden), articulos=articulos, MOTIVOS_PAUSA=MOTIVOS_PAUSA)


def cambiar_estado(oid, permitido_desde, nuevo, roles, **campos):
    orden = obtener_orden(oid)
    if g.usuario["rol"] not in roles:
        abort(403)
    if orden["estado"] not in permitido_desde:
        flash(f"No se puede pasar de «{orden['estado']}» a «{nuevo}».", "error")
        return None
    sets = ", ".join(["estado=?"] + [f"{c}=?" for c in campos])
    bd().execute(f"UPDATE orden SET {sets} WHERE id=?", (nuevo, *campos.values(), oid))
    return orden


@app.post("/ordenes/<int:oid>/asignar")
@requiere("admin", "director")
def orden_asignar(oid):
    tecnico_id = int(request.form["tecnico_id"])
    programada = request.form["programada_para"].replace("T", " ")
    if len(programada) == 16:
        programada += ":00"
    orden = cambiar_estado(oid, ("En espera", "Asignada"), "Asignada", ("admin", "director"),
                           tecnico_id=tecnico_id, programada_para=programada)
    if orden:
        tec = bd().execute("SELECT nombre FROM tecnico WHERE id=?", (tecnico_id,)).fetchone()["nombre"]
        apto = bd().execute("SELECT 1 FROM tecnico_capacidad WHERE tecnico_id=? AND capacidad_id=?",
                            (tecnico_id, orden["capacidad_id"])).fetchone()
        tipo = "Reasignación" if orden["tecnico_id"] else "Asignación"
        evento(oid, tipo, f"{tec} para el {formato_fecha(programada)}")
        auditar("Órdenes", tipo, f"OT-{oid:04d}", f"Técnico anterior: {orden['tecnico'] or '—'}; nuevo: {tec}")
        bd().commit()
        flash(f"Orden asignada a {tec}. (Aviso por correo a {orden['correo']}: pendiente, RF15)", "ok")
        if not apto:
            flash(f"Atención: {tec} no tiene la capacidad que pide la plantilla.", "aviso")
    return redirect(url_for("orden_detalle", oid=oid))


@app.post("/ordenes/<int:oid>/iniciar")
@requiere("tecnico", "admin")
def orden_iniciar(oid):
    if cambiar_estado(oid, ("Asignada",), "En ejecución", ("tecnico", "admin"), inicio=ahora()):
        evento(oid, "Inicio")
        auditar("Órdenes", "Inicio de ejecución", f"OT-{oid:04d}")
        bd().commit()
    return redirect(url_for("orden_detalle", oid=oid))


@app.post("/ordenes/<int:oid>/pausar")
@requiere("tecnico", "admin")
def orden_pausar(oid):
    motivo = request.form["motivo"]
    if cambiar_estado(oid, ("En ejecución",), "Suspendida", ("tecnico", "admin")):
        bd().execute("INSERT INTO pausa (orden_id, motivo, inicio) VALUES (?,?,?)", (oid, motivo, ahora()))
        evento(oid, "Pausa", motivo)
        auditar("Órdenes", "Pausa", f"OT-{oid:04d}", motivo)
        bd().commit()
    return redirect(url_for("orden_detalle", oid=oid))


@app.post("/ordenes/<int:oid>/reanudar")
@requiere("tecnico", "admin")
def orden_reanudar(oid):
    if cambiar_estado(oid, ("Suspendida",), "En ejecución", ("tecnico", "admin")):
        bd().execute("UPDATE pausa SET fin=? WHERE orden_id=? AND fin IS NULL", (ahora(), oid))
        evento(oid, "Reanudación")
        auditar("Órdenes", "Reanudación", f"OT-{oid:04d}")
        bd().commit()
    return redirect(url_for("orden_detalle", oid=oid))


@app.post("/ordenes/<int:oid>/cerrar")
@requiere("tecnico", "admin")
def orden_cerrar(oid):
    diagnostico = request.form.get("diagnostico", "").strip()
    solucion = request.form.get("solucion", "").strip()
    if not diagnostico or not solucion:
        flash("Para cerrar la orden escribe el diagnóstico y la solución.", "error")
        return redirect(url_for("orden_detalle", oid=oid))
    if cambiar_estado(oid, ("En ejecución",), "Finalizada", ("tecnico", "admin"),
                      fin=ahora(), diagnostico=diagnostico, solucion=solucion):
        evento(oid, "Cierre", diagnostico)
        auditar("Órdenes", "Cierre", f"OT-{oid:04d}")
        bd().commit()
        flash("Orden finalizada.", "ok")
    return redirect(url_for("orden_detalle", oid=oid))


@app.post("/ordenes/<int:oid>/anular")
@requiere("admin", "director")
def orden_anular(oid):
    motivo = request.form.get("motivo", "").strip() or "Sin motivo"
    if cambiar_estado(oid, ("En espera", "Asignada"), "Anulada", ("admin", "director")):
        evento(oid, "Anulación", motivo)
        auditar("Órdenes", "Anulación", f"OT-{oid:04d}", motivo)
        bd().commit()
    return redirect(url_for("orden_detalle", oid=oid))


# ---------------------------------------------------------------- inventario (RF11, RF12)

def existencias_bodega(bodega_id):
    return bd().execute("""
        SELECT a.*, COALESCE(SUM(CASE WHEN m.bodega_destino_id=:b THEN m.cantidad
                                      WHEN m.bodega_origen_id=:b THEN -m.cantidad END), 0) AS existencia
        FROM articulo a LEFT JOIN movimiento m ON m.articulo_id = a.id
        WHERE a.activo = 1 GROUP BY a.id ORDER BY a.nombre""", {"b": bodega_id}).fetchall()


@app.route("/inventario")
@requiere("admin", "director", "almacenista")
def inventario():
    bodega_id = request.args.get("bodega", 1, type=int)
    bodegas = bd().execute("SELECT * FROM bodega ORDER BY tipo DESC, nombre").fetchall()
    filas = existencias_bodega(bodega_id)
    if bodega_id != 1:
        filas = [f for f in filas if f["existencia"]]
    return render_template("inventario.html", bodegas=bodegas, bodega_id=bodega_id, filas=filas,
                           articulos=opciones_fk("articulo"))


@app.post("/inventario/entrada")
@requiere("admin", "almacenista")
def inventario_entrada():
    articulo_id = int(request.form["articulo_id"])
    cantidad = int(request.form["cantidad"])
    if cantidad <= 0:
        flash("La cantidad debe ser mayor que cero.", "error")
        return redirect(url_for("inventario"))
    mid = bd().execute(
        "INSERT INTO movimiento (tipo, fecha, articulo_id, cantidad, bodega_destino_id, proveedor, factura, usuario) "
        "VALUES ('Entrada',?,?,?,1,?,?,?)",
        (ahora(), articulo_id, cantidad, request.form.get("proveedor"), request.form.get("factura"),
         g.usuario["usuario"])).lastrowid
    auditar("Inventario", "Entrada por compra", f"Movimiento #{mid}", f"Artículo {articulo_id} x {cantidad}")
    bd().commit()
    flash("Entrada registrada en la bodega principal.", "ok")
    return redirect(url_for("inventario"))


@app.post("/ordenes/<int:oid>/material")
@requiere("admin", "director", "almacenista")
def orden_material(oid):
    orden = obtener_orden(oid)
    articulo_id = int(request.form["articulo_id"])
    cantidad = int(request.form["cantidad"])
    disponible = next((a["existencia"] for a in existencias_bodega(1) if a["id"] == articulo_id), 0)
    # RF12: no se traslada más de lo que hay en la bodega principal.
    if cantidad <= 0 or cantidad > disponible:
        flash(f"Cantidad no válida: en la bodega principal hay {disponible}.", "error")
        return redirect(url_for("orden_detalle", oid=oid))
    destino = bd().execute("SELECT id FROM bodega WHERE cuenta_id=?", (orden["cuenta_id"],)).fetchone()["id"]
    bd().execute(
        "INSERT INTO movimiento (tipo, fecha, articulo_id, cantidad, bodega_origen_id, bodega_destino_id, "
        "orden_id, usuario) VALUES ('Traslado',?,?,?,1,?,?,?)",
        (ahora(), articulo_id, cantidad, destino, oid, g.usuario["usuario"]))
    nombre = bd().execute("SELECT nombre FROM articulo WHERE id=?", (articulo_id,)).fetchone()["nombre"]
    evento(oid, "Traslado de material", f"{cantidad} x {nombre} a la bodega de {orden['cuenta']}")
    auditar("Inventario", "Traslado", f"OT-{oid:04d}", f"{cantidad} x {nombre}")
    bd().commit()
    flash("Material trasladado a la bodega de la cuenta.", "ok")
    return redirect(url_for("orden_detalle", oid=oid))


@app.route("/inventario/kardex/<int:aid>")
@requiere("admin", "director", "almacenista")
def kardex(aid):
    articulo = bd().execute("SELECT * FROM articulo WHERE id=?", (aid,)).fetchone() or abort(404)
    movimientos = bd().execute(
        "SELECT m.*, bo.nombre AS origen, bd.nombre AS destino FROM movimiento m "
        "LEFT JOIN bodega bo ON bo.id=m.bodega_origen_id JOIN bodega bd ON bd.id=m.bodega_destino_id "
        "WHERE m.articulo_id=? ORDER BY m.fecha, m.id", (aid,)).fetchall()
    saldo, filas = 0, []
    for m in movimientos:
        if m["tipo"] == "Entrada":
            saldo += m["cantidad"]
        elif m["bodega_origen_id"] == 1:
            saldo -= m["cantidad"]
        filas.append((m, saldo))
    return render_template("kardex.html", articulo=articulo, filas=filas)


# ---------------------------------------------------------------- auditoría e informes (RF13, RF14)

@app.route("/auditoria")
@requiere("admin")
def auditoria():
    filtros, params = [], []
    for campo in ("usuario", "modulo"):
        if request.args.get(campo):
            filtros.append(f"{campo}=?")
            params.append(request.args[campo])
    where = (" WHERE " + " AND ".join(filtros)) if filtros else ""
    registros = bd().execute(f"SELECT * FROM auditoria{where} ORDER BY id DESC LIMIT 300", params).fetchall()
    usuarios = [r[0] for r in bd().execute("SELECT DISTINCT usuario FROM auditoria ORDER BY 1")]
    modulos = [r[0] for r in bd().execute("SELECT DISTINCT modulo FROM auditoria ORDER BY 1")]
    return render_template("auditoria.html", registros=registros, usuarios=usuarios, modulos=modulos)


@app.route("/informes/tiempos")
@requiere("admin", "director")
def informe_tiempos():
    ordenes = bd().execute(CONSULTA_ORDENES + " WHERE o.estado='Finalizada' ORDER BY t.nombre, o.fin").fetchall()
    resumen = {}
    detalle = []
    for o in ordenes:
        real = tiempo_real(o)
        detalle.append((o, real))
        r = resumen.setdefault(o["tecnico"], {"ordenes": 0, "estimado": 0, "real": 0})
        r["ordenes"] += 1
        r["estimado"] += o["tiempo_estimado"]
        r["real"] += real
    return render_template("informe_tiempos.html", resumen=resumen, detalle=detalle)


@app.errorhandler(403)
def prohibido(_):
    return render_template("error.html", mensaje="Tu rol no tiene permiso para esta acción."), 403


if __name__ == "__main__":
    if not db.RUTA_BD.exists():
        db.crear_bd()
    app.run(debug=True)
