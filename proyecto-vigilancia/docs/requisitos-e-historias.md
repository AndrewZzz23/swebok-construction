# VigiControl · Requisitos e historias de usuario

**Proyecto:** VigiControl – Minuta digital de vigilancia
**Grupo:** G8 · Empresa de vigilancia
**Categoría:** software de gestión · **Dominio:** gestión de servicios
**Metodología:** ágil (Scrum adaptado) · **Prototipo:** Python 3 + Flask + SQLite (software libre)

## 1. Problema

En una empresa de vigilancia, los vigilantes anotan su llegada y las novedades del turno en un libro de minuta de papel que está en cada puesto. El supervisor no sabe en tiempo real quién llegó, quién llegó tarde ni qué pasó. Cuando una novedad es técnica (una cámara que no graba, una puerta que no abre), el aviso al técnico se hace por teléfono y nadie registra cuándo llegó ni cómo se resolvió.

## 2. Actores

| Actor | Descripción |
|---|---|
| Vigilante | Marca llegada y salida de su turno y registra las novedades del puesto. |
| Técnico | Atiende las novedades técnicas que le asignan: marca su llegada y las cierra con la solución. |
| Supervisor | Gestiona puestos, personal y turnos, asigna novedades técnicas y consulta el panel. |

## 3. Requisitos funcionales

| ID | Requisito | Prototipo |
|---|---|---|
| RF01 | Iniciar sesión con usuario y contraseña; cada rol ve solo sus opciones. | ✔ |
| RF02 | Gestionar puestos de vigilancia: cliente, nombre y dirección (crear, editar, inactivar). | ✔ |
| RF03 | Gestionar el personal (vigilantes, técnicos y supervisores): crear, editar, inactivar. | ✔ |
| RF04 | Programar turnos: vigilante, puesto, fecha, hora de entrada y duración, sin cruces de horario. | ✔ |
| RF05 | Marcar llegada y salida del turno. Si la llegada es más de 10 minutos después de la hora de entrada, queda marcada como **tarde**. | ✔ |
| RF06 | Registrar novedades (seguridad, técnica u otra) con descripción, solo durante un turno en curso. | ✔ |
| RF07 | Consultar la minuta de un puesto: llegadas, salidas y novedades en orden. | ✔ |
| RF08 | Asignar una novedad técnica a un técnico; el técnico marca su llegada y la cierra con la solución. | ✔ |
| RF09 | Panel del supervisor: vigilantes en turno, turnos sin llegada, llegadas tarde y novedades técnicas abiertas. | ✔ |
| RF10 | Adjuntar foto a la novedad y registrar la ubicación GPS al marcar. | Pendiente |

**Cobertura del prototipo: 9 de 10 requisitos (90 %).**

## 4. Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF01 | Las contraseñas se guardan cifradas con hash. |
| RNF02 | No se borra información: los puestos y las personas se inactivan. |
| RNF03 | Se usa desde el navegador del celular o del computador (diseño adaptable). |
| RNF04 | Solo software libre: Python, Flask, SQLite, PlantUML, VS Code. |

## 5. Reglas de negocio

- Tolerancia de llegada: 10 minutos.
- Se puede marcar la llegada desde 1 hora antes del inicio del turno.
- Un vigilante no puede tener dos turnos que se crucen.
- Solo se registran novedades después de marcar la llegada.
- Estados de una novedad técnica: Registrada → Asignada → En atención → Cerrada.

## 6. Historias de usuario

Formato: *Como* rol *quiero* acción *para* beneficio. Prioridad MoSCoW. Estimación en puntos (Fibonacci).

| HU | Historia | Criterios de aceptación | Prior. | Pts | Sprint |
|---|---|---|---|---|---|
| HU01 | Como **usuario** quiero iniciar sesión para usar las funciones de mi rol. | Con datos correctos entra a su pantalla; con datos incorrectos ve un mensaje de error. Un vigilante no puede abrir el panel del supervisor. | M | 2 | 1 |
| HU02 | Como **supervisor** quiero registrar los puestos para saber dónde hay vigilancia. | Puedo crear, editar e inactivar. Cliente, nombre y dirección son obligatorios. | M | 2 | 1 |
| HU03 | Como **supervisor** quiero registrar al personal para darles acceso. | Puedo crear, editar e inactivar. El usuario no se puede repetir y la contraseña tiene al menos 6 caracteres. | M | 3 | 1 |
| HU04 | Como **supervisor** quiero programar turnos para cubrir los puestos. | Elijo vigilante, puesto, fecha, hora y duración (8 o 12 h). No se permite un turno que se cruce con otro del mismo vigilante. | M | 3 | 1 |
| HU05 | Como **vigilante** quiero marcar mi llegada y salida para que quede registro de mi turno. | Si llego más de 10 min tarde queda marcado "Tarde". No puedo marcar la salida sin haber marcado la llegada. | M | 5 | 2 |
| HU06 | Como **vigilante** quiero registrar las novedades del turno para no usar la minuta de papel. | Elijo el tipo y escribo qué pasó. Solo puedo hacerlo con la llegada marcada. | M | 3 | 2 |
| HU07 | Como **supervisor** quiero ver la minuta de cada puesto para saber todo lo que pasó. | Muestra llegadas, salidas y novedades, de la más reciente a la más antigua. | M | 3 | 2 |
| HU08 | Como **supervisor** quiero asignar las novedades técnicas a un técnico para que se resuelvan. | Solo se asignan novedades técnicas que no se han empezado a atender. El técnico ve la novedad en "Mis asignaciones". | M | 3 | 3 |
| HU09 | Como **técnico** quiero marcar mi llegada y cerrar la novedad con la solución para dejar constancia del trabajo. | Primero marco la llegada (En atención) y luego cierro con la solución (Cerrada). La solución aparece en la minuta. | M | 5 | 3 |
| HU10 | Como **supervisor** quiero un panel con el estado de los turnos para reaccionar a tiempo. | Muestra cuántos vigilantes están en turno, turnos sin llegada, llegadas tarde y novedades técnicas abiertas. | S | 5 | 3 |
| HU11 | Como **vigilante** quiero adjuntar una foto y mi ubicación para que la novedad tenga evidencia. | La foto se guarda con la novedad y la marcación guarda el GPS. | C | 8 | Backlog |

## 7. Planeación ágil (Scrum adaptado)

| Sprint | Objetivo | Historias | Puntos |
|---|---|---|---|
| 0 | Análisis y diseño: requisitos, historias y diagramas UML | — | — |
| 1 | Acceso y datos básicos | HU01 – HU04 | 10 |
| 2 | El turno del vigilante | HU05 – HU07 | 11 |
| 3 | Novedades técnicas y panel | HU08 – HU10 | 13 |
| Backlog | Siguiente versión | HU11 | 8 |

Definición de terminado: la historia cumple sus criterios de aceptación y funciona en el prototipo.
