"""VigiControl - Minuta digital de vigilancia (prototipo).

Ejecutar:  python app.py   y abrir http://localhost:5000
"""
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db

app = Flask(__name__)
app.secret_key = "vigicontrol-prototipo-academico"

ROLES = {"supervisor": "Supervisor", "vigilante": "Vigilante", "tecnico": "Técnico"}
TIPOS_NOVEDAD = ["Seguridad", "Técnica", "Otra"]
TOLERANCIA_MIN = 10       # minutos de gracia antes de marcar "tarde"
ANTICIPACION_MIN = 60     # se puede marcar llegada hasta 1 hora antes del turno


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
    return datetime.now().replace(microsecond=0)


def requiere(*roles):
    """RF01: hay que iniciar sesión, y cada rol entra solo a lo suyo."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not g.usuario:
                return redirect(url_for("login"))
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
    return {"usuario": g.get("usuario"), "ROLES": ROLES}


@app.template_filter("fecha")
def formato_fecha(valor):
    return datetime.fromisoformat(valor).strftime("%d/%m/%Y %H:%M") if valor else "—"


@app.template_filter("hora")
def formato_hora(valor):
    return datetime.fromisoformat(valor).strftime("%H:%M") if valor else "—"


@app.errorhandler(403)
def prohibido(_):
    return render_template("error.html", mensaje="Tu rol no tiene permiso para esta acción."), 403


# ---------------------------------------------------------------- sesión (RF01)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = bd().execute("SELECT * FROM usuario WHERE usuario=? AND activo=1",
                         (request.form["usuario"].strip(),)).fetchone()
        if u and check_password_hash(u["clave_hash"], request.form["clave"]):
            session["uid"] = u["id"]
            return redirect(url_for("inicio"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@requiere()
def inicio():
    destino = {"supervisor": "panel", "vigilante": "mi_turno", "tecnico": "mis_asignaciones"}
    return redirect(url_for(destino[g.usuario["rol"]]))


# ---------------------------------------------------------------- puestos y personal (RF02, RF03)

@app.route("/puestos", methods=["GET", "POST"])
@requiere("supervisor")
def puestos():
    editar = request.args.get("editar", type=int)
    if request.method == "POST":
        datos = [request.form[c].strip() for c in ("nombre", "cliente", "direccion")]
        if not all(datos):
            flash("Todos los campos son obligatorios.", "error")
        elif editar:
            bd().execute("UPDATE puesto SET nombre=?, cliente=?, direccion=? WHERE id=?", (*datos, editar))
            bd().commit()
            flash("Puesto actualizado.", "ok")
            return redirect(url_for("puestos"))
        else:
            bd().execute("INSERT INTO puesto (nombre, cliente, direccion) VALUES (?,?,?)", datos)
            bd().commit()
            flash("Puesto creado.", "ok")
            return redirect(url_for("puestos"))
    lista = bd().execute("SELECT * FROM puesto ORDER BY activo DESC, cliente").fetchall()
    actual = bd().execute("SELECT * FROM puesto WHERE id=?", (editar,)).fetchone() if editar else None
    return render_template("puestos.html", puestos=lista, actual=actual)


@app.route("/personal", methods=["GET", "POST"])
@requiere("supervisor")
def personal():
    editar = request.args.get("editar", type=int)
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        usuario = request.form["usuario"].strip()
        clave = request.form.get("clave", "")
        rol = request.form["rol"]
        celular = request.form.get("celular", "").strip()
        repetido = bd().execute("SELECT 1 FROM usuario WHERE usuario=? AND id IS NOT ?", (usuario, editar)).fetchone()
        if not nombre or not usuario or rol not in ROLES:
            flash("Nombre, usuario y rol son obligatorios.", "error")
        elif repetido:
            flash(f"El usuario «{usuario}» ya existe.", "error")
        elif not editar and len(clave) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
        else:
            if editar:
                bd().execute("UPDATE usuario SET nombre=?, usuario=?, rol=?, celular=? WHERE id=?",
                             (nombre, usuario, rol, celular, editar))
                if clave:
                    bd().execute("UPDATE usuario SET clave_hash=? WHERE id=?", (generate_password_hash(clave), editar))
            else:
                bd().execute("INSERT INTO usuario (nombre, usuario, clave_hash, rol, celular) VALUES (?,?,?,?,?)",
                             (nombre, usuario, generate_password_hash(clave), rol, celular))
            bd().commit()
            flash("Persona guardada.", "ok")
            return redirect(url_for("personal"))
    lista = bd().execute("SELECT * FROM usuario ORDER BY activo DESC, rol, nombre").fetchall()
    actual = bd().execute("SELECT * FROM usuario WHERE id=?", (editar,)).fetchone() if editar else None
    return render_template("personal.html", personas=lista, actual=actual)


@app.post("/<any(puesto, usuario):tabla>/<int:rid>/estado")
@requiere("supervisor")
def cambiar_estado(tabla, rid):
    """No se borra nada: se inactiva o se vuelve a activar."""
    if tabla == "usuario" and rid == g.usuario["id"]:
        flash("No puedes inactivar tu propio usuario.", "error")
    else:
        bd().execute(f"UPDATE {tabla} SET activo = 1 - activo WHERE id=?", (rid,))
        bd().commit()
    return redirect(url_for("puestos" if tabla == "puesto" else "personal"))


# ---------------------------------------------------------------- turnos (RF04, RF05)

CONSULTA_TURNOS = """
SELECT t.*, u.nombre AS vigilante, p.nombre AS puesto, p.cliente,
       ll.fecha AS llegada, ll.tarde, sa.fecha AS salida
FROM turno t
JOIN usuario u ON u.id = t.vigilante_id
JOIN puesto p ON p.id = t.puesto_id
LEFT JOIN marcacion ll ON ll.turno_id = t.id AND ll.tipo = 'Llegada'
LEFT JOIN marcacion sa ON sa.turno_id = t.id AND sa.tipo = 'Salida'
"""


def estado_turno(t):
    momento = ahora()
    inicio = datetime.fromisoformat(t["inicio"])
    fin = datetime.fromisoformat(t["fin"])
    if t["salida"]:
        return "Terminado"
    if t["llegada"]:
        return "En curso"
    if momento > fin:
        return "No se presentó"
    if momento > inicio + timedelta(minutes=TOLERANCIA_MIN):
        return "Sin llegada"
    return "Programado"


@app.route("/turnos", methods=["GET", "POST"])
@requiere("supervisor")
def turnos():
    if request.method == "POST":
        inicio = datetime.fromisoformat(f"{request.form['fecha']} {request.form['hora']}")
        fin = inicio + timedelta(hours=int(request.form["horas"]))
        vigilante = int(request.form["vigilante_id"])
        cruce = bd().execute("SELECT 1 FROM turno WHERE vigilante_id=? AND inicio < ? AND fin > ?",
                             (vigilante, db.hora(fin), db.hora(inicio))).fetchone()
        if cruce:
            flash("Ese vigilante ya tiene un turno que se cruza con ese horario.", "error")
        else:
            bd().execute("INSERT INTO turno (vigilante_id, puesto_id, inicio, fin) VALUES (?,?,?,?)",
                         (vigilante, int(request.form["puesto_id"]), db.hora(inicio), db.hora(fin)))
            bd().commit()
            flash("Turno programado.", "ok")
            return redirect(url_for("turnos"))
    desde = db.hora(ahora() - timedelta(days=2))
    lista = bd().execute(CONSULTA_TURNOS + " WHERE t.fin >= ? ORDER BY t.inicio", (desde,)).fetchall()
    vigilantes = bd().execute("SELECT id, nombre FROM usuario WHERE rol='vigilante' AND activo=1 ORDER BY nombre").fetchall()
    lista_puestos = bd().execute("SELECT id, cliente || ' — ' || nombre AS nombre FROM puesto WHERE activo=1 ORDER BY 2").fetchall()
    return render_template("turnos.html", turnos=[(t, estado_turno(t)) for t in lista], vigilantes=vigilantes,
                           puestos=lista_puestos, hoy=ahora().strftime("%Y-%m-%d"))


def turno_actual(vigilante_id):
    """El turno en curso del vigilante, o el próximo que ya puede marcar."""
    momento = ahora()
    en_curso = bd().execute(CONSULTA_TURNOS + " WHERE t.vigilante_id=? AND ll.id IS NOT NULL AND sa.id IS NULL",
                            (vigilante_id,)).fetchone()
    if en_curso:
        return en_curso
    return bd().execute(
        CONSULTA_TURNOS + " WHERE t.vigilante_id=? AND ll.id IS NULL AND t.inicio <= ? AND t.fin > ? ORDER BY t.inicio",
        (vigilante_id, db.hora(momento + timedelta(minutes=ANTICIPACION_MIN)), db.hora(momento))).fetchone()


@app.route("/mi-turno")
@requiere("vigilante")
def mi_turno():
    turno = turno_actual(g.usuario["id"])
    novedades = []
    if turno:
        novedades = bd().execute(
            "SELECT n.*, u.nombre AS autor FROM novedad n JOIN usuario u ON u.id = n.reportada_por "
            "WHERE n.puesto_id=? ORDER BY n.fecha DESC LIMIT 5", (turno["puesto_id"],)).fetchall()
    proximos = bd().execute(CONSULTA_TURNOS + " WHERE t.vigilante_id=? AND t.inicio > ? ORDER BY t.inicio LIMIT 3",
                            (g.usuario["id"], db.hora(ahora()))).fetchall()
    return render_template("mi_turno.html", turno=turno, novedades=novedades, proximos=proximos,
                           TIPOS=TIPOS_NOVEDAD, TOLERANCIA=TOLERANCIA_MIN)


@app.post("/turnos/<int:tid>/<any(llegada, salida):accion>")
@requiere("vigilante")
def marcar(tid, accion):
    turno = turno_actual(g.usuario["id"])
    if not turno or turno["id"] != tid:
        flash("Ese turno no está disponible para marcar.", "error")
        return redirect(url_for("mi_turno"))
    momento = ahora()
    if accion == "llegada":
        if turno["llegada"]:
            flash("La llegada ya estaba marcada.", "error")
            return redirect(url_for("mi_turno"))
        # RF05: si llega después de la tolerancia, queda marcado como tarde.
        tarde = momento > datetime.fromisoformat(turno["inicio"]) + timedelta(minutes=TOLERANCIA_MIN)
        bd().execute("INSERT INTO marcacion (turno_id, tipo, fecha, tarde) VALUES (?,?,?,?)",
                     (tid, "Llegada", db.hora(momento), int(tarde)))
        flash("Llegada marcada" + (" (tarde)." if tarde else " a tiempo."), "aviso" if tarde else "ok")
    else:
        if not turno["llegada"]:
            flash("Primero debes marcar la llegada.", "error")
            return redirect(url_for("mi_turno"))
        bd().execute("INSERT INTO marcacion (turno_id, tipo, fecha) VALUES (?,?,?)", (tid, "Salida", db.hora(momento)))
        flash("Salida marcada. ¡Buen descanso!", "ok")
    bd().commit()
    return redirect(url_for("mi_turno"))


# ---------------------------------------------------------------- novedades (RF06, RF07, RF08)

CONSULTA_NOVEDADES = """
SELECT n.*, p.nombre AS puesto, p.cliente, p.direccion, a.nombre AS autor, t.nombre AS tecnico
FROM novedad n
JOIN puesto p ON p.id = n.puesto_id
JOIN usuario a ON a.id = n.reportada_por
LEFT JOIN usuario t ON t.id = n.tecnico_id
"""


@app.post("/novedades")
@requiere("vigilante")
def registrar_novedad():
    turno = turno_actual(g.usuario["id"])
    tipo = request.form.get("tipo")
    descripcion = request.form.get("descripcion", "").strip()
    # RF06: solo se registran novedades durante un turno en curso.
    if not turno or not turno["llegada"]:
        flash("Debes marcar la llegada a tu turno antes de registrar novedades.", "error")
    elif tipo not in TIPOS_NOVEDAD or not descripcion:
        flash("Elige el tipo y escribe la descripción.", "error")
    else:
        bd().execute("INSERT INTO novedad (puesto_id, turno_id, reportada_por, fecha, tipo, descripcion) "
                     "VALUES (?,?,?,?,?,?)",
                     (turno["puesto_id"], turno["id"], g.usuario["id"], db.hora(ahora()), tipo, descripcion))
        bd().commit()
        flash("Novedad registrada en la minuta." +
              (" El supervisor la asignará a un técnico." if tipo == "Técnica" else ""), "ok")
    return redirect(url_for("mi_turno"))


@app.route("/novedades")
@requiere("supervisor")
def novedades():
    filtros, params = [], []
    for campo in ("tipo", "estado"):
        if request.args.get(campo):
            filtros.append(f"n.{campo}=?")
            params.append(request.args[campo])
    where = (" WHERE " + " AND ".join(filtros)) if filtros else ""
    lista = bd().execute(CONSULTA_NOVEDADES + where + " ORDER BY n.fecha DESC", params).fetchall()
    tecnicos = bd().execute("SELECT id, nombre FROM usuario WHERE rol='tecnico' AND activo=1 ORDER BY nombre").fetchall()
    return render_template("novedades.html", novedades=lista, tecnicos=tecnicos, TIPOS=TIPOS_NOVEDAD,
                           ESTADOS=["Registrada", "Asignada", "En atención", "Cerrada"])


@app.post("/novedades/<int:nid>/asignar")
@requiere("supervisor")
def asignar_novedad(nid):
    novedad = bd().execute("SELECT * FROM novedad WHERE id=?", (nid,)).fetchone() or abort(404)
    if novedad["tipo"] != "Técnica" or novedad["estado"] not in ("Registrada", "Asignada"):
        flash("Solo se asignan novedades técnicas que no se han empezado a atender.", "error")
    else:
        bd().execute("UPDATE novedad SET tecnico_id=?, estado='Asignada' WHERE id=?",
                     (int(request.form["tecnico_id"]), nid))
        bd().commit()
        flash("Novedad asignada al técnico.", "ok")
    volver = request.form.get("volver", "")
    return redirect(volver if volver.startswith("/") else url_for("novedades"))


@app.route("/mis-asignaciones")
@requiere("tecnico")
def mis_asignaciones():
    lista = bd().execute(CONSULTA_NOVEDADES + " WHERE n.tecnico_id=? ORDER BY n.estado='Cerrada', n.fecha",
                         (g.usuario["id"],)).fetchall()
    return render_template("mis_asignaciones.html", novedades=lista)


@app.post("/novedades/<int:nid>/<any(llegada, cerrar):accion>")
@requiere("tecnico")
def atender_novedad(nid, accion):
    novedad = bd().execute("SELECT * FROM novedad WHERE id=? AND tecnico_id=?", (nid, g.usuario["id"])).fetchone()
    if not novedad:
        abort(403)
    if accion == "llegada" and novedad["estado"] == "Asignada":
        bd().execute("UPDATE novedad SET estado='En atención', llegada_tecnico=? WHERE id=?", (db.hora(ahora()), nid))
        flash("Llegada al puesto marcada.", "ok")
    elif accion == "cerrar" and novedad["estado"] == "En atención":
        solucion = request.form.get("solucion", "").strip()
        if not solucion:
            flash("Escribe la solución para cerrar la novedad.", "error")
            return redirect(url_for("mis_asignaciones"))
        bd().execute("UPDATE novedad SET estado='Cerrada', cerrada_en=?, solucion=? WHERE id=?",
                     (db.hora(ahora()), solucion, nid))
        flash("Novedad cerrada.", "ok")
    else:
        flash("Esa acción no corresponde al estado de la novedad.", "error")
    bd().commit()
    return redirect(url_for("mis_asignaciones"))


@app.route("/minuta/<int:pid>")
@requiere("supervisor", "vigilante")
def minuta(pid):
    """RF07: la minuta del puesto, con marcaciones y novedades en orden."""
    if g.usuario["rol"] == "vigilante":
        turno = turno_actual(g.usuario["id"])
        if not turno or turno["puesto_id"] != pid:
            abort(403)
    puesto = bd().execute("SELECT * FROM puesto WHERE id=?", (pid,)).fetchone() or abort(404)
    marcaciones = bd().execute(
        "SELECT m.fecha, m.tipo, m.tarde, u.nombre FROM marcacion m JOIN turno t ON t.id=m.turno_id "
        "JOIN usuario u ON u.id=t.vigilante_id WHERE t.puesto_id=?", (pid,)).fetchall()
    lista = bd().execute(CONSULTA_NOVEDADES + " WHERE n.puesto_id=?", (pid,)).fetchall()
    registros = [{"fecha": m["fecha"], "clase": "marcacion",
                  "texto": f"{m['nombre']} marcó {m['tipo'].lower()}" + (" (tarde)" if m["tarde"] else "")}
                 for m in marcaciones]
    for n in lista:
        registros.append({"fecha": n["fecha"], "clase": "novedad", "tipo": n["tipo"], "estado": n["estado"],
                          "texto": n["descripcion"], "autor": n["autor"], "tecnico": n["tecnico"],
                          "solucion": n["solucion"]})
    registros.sort(key=lambda r: r["fecha"], reverse=True)
    return render_template("minuta.html", puesto=puesto, registros=registros)


# ---------------------------------------------------------------- panel del supervisor (RF09)

@app.route("/panel")
@requiere("supervisor")
def panel():
    momento = ahora()
    desde = db.hora(momento - timedelta(days=1))
    hoy = bd().execute(CONSULTA_TURNOS + " WHERE t.fin >= ? AND t.inicio <= ? ORDER BY t.inicio",
                       (db.hora(momento), db.hora(momento + timedelta(hours=1)))).fetchall()
    con_estado = [(t, estado_turno(t)) for t in hoy]
    abiertas = bd().execute(CONSULTA_NOVEDADES + " WHERE n.tipo='Técnica' AND n.estado!='Cerrada' ORDER BY n.fecha").fetchall()
    recientes = bd().execute(CONSULTA_NOVEDADES + " WHERE n.fecha >= ? ORDER BY n.fecha DESC LIMIT 6", (desde,)).fetchall()
    tecnicos = bd().execute("SELECT id, nombre FROM usuario WHERE rol='tecnico' AND activo=1 ORDER BY nombre").fetchall()
    resumen = {
        "en_turno": sum(1 for _, e in con_estado if e == "En curso"),
        "sin_llegada": sum(1 for _, e in con_estado if e == "Sin llegada"),
        "tarde": sum(1 for t, e in con_estado if e == "En curso" and t["tarde"]),
        "abiertas": len(abiertas),
    }
    return render_template("panel.html", turnos=con_estado, abiertas=abiertas, recientes=recientes,
                           tecnicos=tecnicos, resumen=resumen)


if __name__ == "__main__":
    if not db.RUTA_BD.exists():
        db.crear_bd()
    app.run(debug=True)
