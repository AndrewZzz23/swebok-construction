# SIGEV · Requisitos e historias de usuario

**Proyecto:** SIGEV – Sistema de Gestión de Servicios de Vigilancia
**Categoría:** software de gestión · **Dominio:** gestión de productos/servicios
**Caso de estudio:** empresa de seguridad electrónica de Ibagué (alarmas, CCTV, control de acceso), basado en el levantamiento de Aguialarmas LTDA.
**Metodología:** ágil (Scrum adaptado) · **Prototipo:** Python 3 + Flask + SQLite (software libre)

## 1. Problema

La empresa atiende a sus clientes en sus sedes ("cuentas") con técnicos de campo. Hoy controla las órdenes de servicio, los tiempos de los técnicos y el inventario de forma manual (llamadas, hojas de cálculo y papel). Esto produce:

- Órdenes duplicadas cuando el cliente llama varias veces por la misma falla.
- Asignaciones a técnicos sin el conocimiento necesario.
- Desconocimiento del tiempo real que toma cada servicio.
- Diferencias entre el inventario registrado y el físico, porque no se sabe qué material quedó en cada sede.

## 2. Actores

| Actor | Descripción |
|---|---|
| Administrador | Configura el sistema, gestiona catálogos y consulta la auditoría. |
| Director técnico | Crea, asigna y supervisa las órdenes; consulta informes. |
| Técnico | Ejecuta las órdenes que tiene asignadas. |
| Almacenista | Maneja los artículos, las entradas por compra y los traslados de material. |

## 3. Requisitos funcionales

| ID | Requisito | Prototipo |
|---|---|---|
| RF01 | Iniciar y cerrar sesión con usuario y contraseña. | ✔ |
| RF02 | Controlar el acceso según el rol (administrador, director técnico, técnico, almacenista). | ✔ |
| RF03 | Gestionar clientes (crear, consultar, editar, inactivar). | ✔ |
| RF04 | Gestionar cuentas o sedes de cada cliente (dirección, contacto, correo, ruta); al crear una cuenta se crea su bodega. | ✔ |
| RF05 | Gestionar técnicos y sus capacidades (CCTV, alarmas, control de acceso…). | ✔ |
| RF06 | Gestionar plantillas de servicio con prioridad, tiempo estimado y capacidad requerida. | ✔ |
| RF07 | Crear órdenes de trabajo con control de duplicados: si existe una orden pendiente de la misma cuenta y plantilla, no se crea otra; se agrega una nota y sube la prioridad. | ✔ |
| RF08 | Asignar y reasignar órdenes a un técnico con fecha y hora, mostrando primero a los técnicos con la capacidad requerida y avisando si se asigna a uno que no la tiene. | ✔ |
| RF09 | Ejecutar la orden: iniciar, pausar con motivo, reanudar y cerrar con diagnóstico y solución. El tiempo en pausa no cuenta. | ✔ |
| RF10 | Tablero de órdenes por estado, con filtros por estado, técnico y cliente, y alerta de tiempo superado. | ✔ |
| RF11 | Gestionar artículos (recuperables o consumibles), registrar entradas por compra y consultar existencias por bodega con aviso de existencia mínima. | ✔ |
| RF12 | Trasladar material de la bodega principal a la bodega de la cuenta de una orden, sin superar la existencia disponible; consultar el kardex por artículo. | ✔ |
| RF13 | Registrar en la auditoría cada acción (usuario, fecha, módulo, acción, registro) y consultarla con filtros. | ✔ |
| RF14 | Informe de tiempos ganados y perdidos por técnico (tiempo real frente al estimado). | ✔ |
| RF15 | Enviar un correo al contacto de la cuenta al asignar o reprogramar una orden. | Pendiente |
| RF16 | Gestionar usuarios (crear, editar, inactivar) desde la aplicación. | Pendiente |
| RF17 | Recuperar la contraseña por correo. | Pendiente |
| RF18 | Registrar la ubicación GPS del técnico en cada marcación desde una app móvil. | Pendiente |
| RF19 | Exportar los informes y la auditoría a Excel. | Pendiente |
| RF20 | Registrar devoluciones y reposiciones de equipos dañados. | Pendiente |

**Cobertura del prototipo: 14 de 20 requisitos (70 %)**, por encima del 50 % exigido.

## 4. Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF01 | Las contraseñas se guardan cifradas con hash (no en texto plano). |
| RNF02 | No se borra información: los registros se inactivan o se anulan. |
| RNF03 | Funciona en navegadores actuales (Chrome, Firefox, Edge) y se adapta a pantallas pequeñas. |
| RNF04 | Se desarrolla solo con software libre: Python, Flask, SQLite, VS Code. |
| RNF05 | Una acción común (crear, asignar, cerrar) se completa en menos de 3 clics desde la orden. |

## 5. Historias de usuario

Formato: *Como* rol *quiero* acción *para* beneficio. Prioridad MoSCoW (M = debe, S = debería, C = podría). Estimación en puntos de historia (Fibonacci).

| HU | Historia | Criterios de aceptación | Prior. | Pts | Sprint |
|---|---|---|---|---|---|
| HU01 | Como **usuario** quiero iniciar sesión con usuario y contraseña para acceder a mis funciones. | Con datos correctos entra a su pantalla de inicio. Con datos incorrectos ve "Usuario o contraseña incorrectos". Al salir, la sesión se cierra. | M | 2 | 1 |
| HU02 | Como **administrador** quiero que cada rol vea solo sus opciones para proteger la información. | Un técnico no puede abrir inventario ni crear órdenes (error 403). El menú muestra solo las opciones del rol. | M | 3 | 1 |
| HU03 | Como **director técnico** quiero registrar clientes para tener sus datos al crear órdenes. | Puedo crear, editar e inactivar. El nombre es obligatorio. Un cliente inactivo no aparece en los formularios. | M | 2 | 1 |
| HU04 | Como **director técnico** quiero registrar las sedes (cuentas) de cada cliente para saber dónde se presta el servicio. | Cada cuenta pertenece a un cliente y tiene dirección, contacto, correo y ruta. Al crearla se crea su bodega. | M | 3 | 1 |
| HU05 | Como **director técnico** quiero registrar los técnicos con sus capacidades para asignar a la persona adecuada. | Puedo marcar varias capacidades por técnico y verlas en la lista. | M | 3 | 1 |
| HU06 | Como **director técnico** quiero definir plantillas de servicio para estandarizar prioridad y tiempo estimado. | Cada plantilla tiene prioridad (alta, media, baja), tiempo estimado en minutos y capacidad requerida. | M | 2 | 1 |
| HU07 | Como **director técnico** quiero crear órdenes sin duplicarlas para no atender dos veces la misma falla. | Se crea la orden en "En espera" con la prioridad de la plantilla. Si ya hay una pendiente de la misma cuenta y plantilla, no se crea otra: se agrega una nota y sube la prioridad. | M | 5 | 2 |
| HU08 | Como **director técnico** quiero asignar la orden a un técnico con fecha y hora para programar el trabajo. | La lista muestra primero a los técnicos con la capacidad (✔). Si elijo uno sin la capacidad, el sistema me avisa. La orden pasa a "Asignada" y queda en la línea de tiempo. | M | 5 | 2 |
| HU09 | Como **técnico** quiero iniciar, pausar, reanudar y cerrar mis órdenes para registrar el trabajo real. | Solo veo mis órdenes. Iniciar → "En ejecución". Pausar pide motivo → "Suspendida". Cerrar exige diagnóstico y solución → "Finalizada". El tiempo real descuenta las pausas. | M | 8 | 2 |
| HU10 | Como **director técnico** quiero ver un tablero por estados para controlar el avance. | Columnas por estado, filtros por estado, técnico y cliente. Las órdenes que superan el tiempo estimado se marcan en rojo. | M | 5 | 2 |
| HU11 | Como **almacenista** quiero registrar artículos y entradas por compra para conocer las existencias. | La entrada suma a la bodega principal con proveedor y factura. Los artículos bajo el mínimo se resaltan. | M | 5 | 3 |
| HU12 | Como **almacenista** quiero trasladar material a la sede de una orden para saber qué quedó instalado. | No se permite trasladar más de lo disponible. El traslado aparece en la orden y en el kardex. | M | 5 | 3 |
| HU13 | Como **administrador** quiero consultar la auditoría para saber quién hizo cada cambio. | Cada acción guarda usuario, fecha, módulo y acción. Puedo filtrar por usuario y módulo. | S | 3 | 3 |
| HU14 | Como **director técnico** quiero un informe de tiempos por técnico para medir la productividad. | Muestra órdenes finalizadas, tiempo estimado, real y la diferencia (ganados o perdidos). | S | 3 | 3 |
| HU15 | Como **cliente** quiero recibir un correo cuando programen mi visita para estar preparado. | Al asignar, se envía un correo al contacto con fecha, hora y técnico. | S | 3 | Backlog |
| HU16 | Como **administrador** quiero gestionar usuarios para dar y quitar accesos. | Crear, editar, inactivar usuarios y asignar rol. | S | 3 | Backlog |
| HU17 | Como **usuario** quiero recuperar mi contraseña por correo para no depender del administrador. | Llega un enlace temporal para cambiarla. | C | 3 | Backlog |
| HU18 | Como **director técnico** quiero ver la ubicación del técnico en cada marcación para validar su llegada. | La app móvil guarda el GPS al llegar, iniciar y cerrar. | C | 13 | Backlog |
| HU19 | Como **director técnico** quiero exportar los informes a Excel para compartirlos. | Botón "Exportar" en informes y auditoría. | C | 2 | Backlog |
| HU20 | Como **almacenista** quiero registrar devoluciones y reposiciones para controlar los equipos dañados. | El equipo dañado queda pendiente hasta que vuelve a bodega. | C | 5 | Backlog |

## 6. Planeación ágil (Scrum adaptado)

| Sprint | Objetivo | Historias | Puntos |
|---|---|---|---|
| 0 | Análisis y diseño: requisitos, historias, diagramas UML | — | — |
| 1 | Acceso y datos maestros | HU01 – HU06 | 15 |
| 2 | Ciclo de vida de las órdenes | HU07 – HU10 | 23 |
| 3 | Inventario, auditoría e informes | HU11 – HU14 | 16 |
| Backlog | Siguiente versión | HU15 – HU20 | 29 |

Artefactos usados: product backlog (tabla de historias), sprint backlog por sprint, tablero Kanban (Por hacer / En curso / Hecho) y definición de terminado: la historia cumple sus criterios de aceptación y pasa la prueba en el prototipo.
