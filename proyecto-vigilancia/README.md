# SIGEV · Sistema de Gestión de Servicios de Vigilancia

Prototipo funcional de un software de gestión para una empresa de seguridad electrónica y vigilancia: órdenes de servicio, técnicos, inventario, auditoría e informes.

- Requisitos e historias de usuario: [docs/requisitos-e-historias.md](docs/requisitos-e-historias.md)
- Diagramas UML (PlantUML): carpeta [uml/](uml/), imágenes en [uml/png/](uml/png/)
- Capturas del prototipo: carpeta [capturas/](capturas/)
- **Demo en vivo en el navegador** (sin instalar nada): [demo/](demo/). Usa Pyodide para ejecutar este mismo código Flask en el navegador, con la base SQLite en memoria.

## Cómo ejecutarlo

Requiere Python 3.10 o superior.

```bash
cd proyecto-vigilancia
pip install -r requirements.txt
python db.py        # crea la base de datos con datos de ejemplo (sigev.db)
python app.py       # abre http://localhost:5000
```

Para volver a los datos de ejemplo, ejecuta otra vez `python db.py`.

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | Administrador |
| director | director123 | Director técnico |
| carlos | tecnico123 | Técnico |
| laura | tecnico123 | Técnico |
| almacen | almacen123 | Almacenista |

## Recorrido sugerido para la demostración

1. Entra como **director**: mira el tablero (la OT-0003 aparece en rojo porque superó el tiempo estimado).
2. Crea una orden nueva para *Clínica San Rafael — Sede Centro* con la plantilla *Revisión de alarma disparada*. Repite la misma orden: el sistema no la duplica, agrega la nota y sube la prioridad.
3. Asígnala: los técnicos con ✔ tienen la capacidad requerida. Si eliges uno con ✖, el sistema avisa.
4. Entra como **carlos**: solo ve sus órdenes. Inicia, pausa, reanuda y cierra la orden.
5. Entra como **almacen**: registra una entrada por compra y traslada material a una orden. Prueba trasladar más de lo disponible.
6. Entra como **admin**: revisa la auditoría y el informe de tiempos.

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
├── app.py            rutas y lógica (sesión, catálogos, órdenes, inventario, auditoría, informes)
├── db.py             esquema SQLite y datos de ejemplo
├── templates/        vistas HTML (Jinja2)
├── static/           estilos
├── uml/              diagramas en PlantUML (.puml) y sus imágenes (png/)
├── docs/             requisitos e historias de usuario
└── capturas/         pantallazos del prototipo
```

Para regenerar los diagramas: `java -jar plantuml.jar -tpng -o png uml/*.puml`, o con la extensión *PlantUML* de VS Code.
