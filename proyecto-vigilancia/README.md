# VigiControl · Minuta digital de vigilancia

Prototipo funcional para una empresa de vigilancia. Los vigilantes marcan su llegada al puesto y registran las novedades del turno. Cuando una novedad es técnica, el supervisor la asigna a un técnico, que marca su llegada y la cierra con la solución.

- Requisitos e historias de usuario: [docs/requisitos-e-historias.md](docs/requisitos-e-historias.md)
- Diagramas UML (PlantUML): carpeta [uml/](uml/), imágenes en [uml/png/](uml/png/)
- Capturas del prototipo: carpeta [capturas/](capturas/)
- **Demo en vivo en el navegador** (sin instalar nada): [demo/](demo/). Usa Pyodide para ejecutar este mismo código Flask en el navegador, con la base SQLite en memoria.

## Cómo ejecutarlo

Requiere Python 3.10 o superior.

```bash
cd proyecto-vigilancia
pip install -r requirements.txt
python db.py        # crea la base de datos con datos de ejemplo (vigicontrol.db)
python app.py       # abre http://localhost:5000
```

Los datos de ejemplo se crean en relación con la hora actual. Para empezar de nuevo, ejecuta otra vez `python db.py`.

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| supervisor | supervisor123 | Supervisor |
| juan | vigilante123 | Vigilante (turno que empieza ahora, sin llegada) |
| maria | vigilante123 | Vigilante (turno en curso, llegó tarde) |
| andres | vigilante123 | Vigilante (no ha llegado a su turno) |
| carlos | tecnico123 | Técnico |
| laura | tecnico123 | Técnico |

## Recorrido para la demostración

1. Entra como **juan**: marca la llegada (a tiempo) y registra una novedad técnica, por ejemplo "La cámara 2 no graba".
2. Entra como **supervisor**: en el panel aparece la novedad abierta, Andrés sin llegada y María tarde. Asigna la novedad a Carlos.
3. Entra como **carlos**: en "Mis asignaciones", marca la llegada al puesto y cierra la novedad con la solución.
4. Vuelve como **supervisor** y abre la minuta de la portería: se ven la llegada de Juan, la novedad y la solución del técnico.

## Tecnologías (software libre)

| Uso | Herramienta |
|---|---|
| Lenguaje | Python 3 |
| Framework web | Flask (plantillas Jinja2) |
| Base de datos | SQLite |
| Herramienta CASE (UML) | PlantUML |
| IDE | Visual Studio Code |

## Estructura

```
proyecto-vigilancia/
├── app.py            rutas y reglas (sesión, puestos, personal, turnos, novedades, minuta, panel)
├── db.py             esquema SQLite y datos de ejemplo
├── templates/        vistas HTML (Jinja2)
├── static/           estilos
├── uml/              diagramas en PlantUML (.puml) y sus imágenes (png/)
├── docs/             requisitos e historias de usuario
├── capturas/         pantallazos del prototipo
└── demo/             la misma app ejecutándose en el navegador (Pyodide)
```

Para regenerar los diagramas: `java -jar plantuml.jar -tpng -o png uml/*.puml`, o con la extensión *PlantUML* de VS Code.
