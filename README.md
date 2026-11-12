# ERP Omnicanal Insumaes Cloud — Arquitectura y Manual de Operaciones (V5)

> **Última actualización:** `2026-11-11 23:52:36` (Chile) | **35 Funciones Activas (Panel 0-24)** | **Stack:** Python, Google Cloud VM, SQLite, WooCommerce API, Mercado Libre API, Dropbox API

---

## 1. Impacto Operativo y Ahorro de Tiempo (Trabajo Manual vs. Arquitectura Cloud)

El sistema transforma procesos manuales repetitivos en operaciones automatizadas por lote en Google Cloud, logrando una **reducción del 95,3% en el tiempo operativo mensual** (**52,5 horas ahorradas al mes** / **630,0 horas al año**, equivalentes a **75,0 jornadas laborales completas** de 8,4 horas):

| Proceso Operativo / Comercial | Volumen Activo | Tiempo Haciéndolo a Mano | Tiempo con Máquina Cloud | Ahorro Mensual | Ahorro Anual |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **1. Sincronización Stock y Precios (Woo + ML)** | 2.509 ítems (550 cambios/mes) | 2,5 min por cambio (23,8 hrs/mes) | 0,35 seg por cambio (0,9 hrs/mes) | **22,9 hrs** | **274,8 hrs** |
| **2. Emisión y Cruce de Cotizaciones B2B** | 141 cotizaciones/mes (445 en SQL) | 8,0 min por cotización (18,8 hrs/mes) | 0,5 min por cotización (1,2 hrs/mes) | **17,6 hrs** | **211,2 hrs** |
| **3. Estandarización HTML/CSS y Auto-Linker ISO** | 752 fichas técnicas vinculadas | 3,5 min por ficha (43,9 hrs por lote) | 4,0 min el lote completo (0,2 hrs/mes) | **7,3 hrs** | **87,6 hrs** |
| **4. Estandarización de Fotos (800x720) y Categorías** | 1.727 productos (100 ajustes/mes) | 3,0 min por imagen (5,0 hrs/mes) | 0,2 min por imagen (0,3 hrs/mes) | **4,7 hrs** | **56,4 hrs** |
| **TOTAL OPERACIÓN CONTINUA** | **2.509 publicaciones + CRM B2B** | **55,1 hrs / mes** | **2,6 hrs / mes** | **52,5 hrs / mes** | **630,0 hrs / año** |

### Velocidad de Ejecución en Tareas Masivas Puntuales (Lotes Complejos)

| Tarea Masiva de Catálogo o Inteligencia Comercial | Haciéndolo a Mano | Con este Sistema Cloud | Reducción de Tiempo |
| :--- | :---: | :---: | :---: |
| **Conectar botones de venta cruzada en 752 productos web** | 43,9 horas (5,2 días) | **4,0 minutos** | **99,8%** |
| **Unificar ~204 Libros de Clientes por Ciudad + Cuentas por Cobrar** | 18,0 horas (2,1 días) | **1,8 minutos** | **99,8%** |
| **Buscar el historial, RUT y cotizaciones de un cliente en 204 ciudades** | 15,0 minutos | **0,01 segundos (SQL)** | **99,9%** |
| **Preparar y estructurar las 1.727 fichas para 1 nuevo Marketplace** | 172,7 horas (20,6 días) | **30,0 minutos (0,5 hrs)** | **99,7%** |
| **Expandir el catálogo completo a 3 nuevos Marketplaces (Falabella, Paris, Lider)** | 518,1 horas (61,7 días) | **1,5 horas** | **99,7%** |

---

## 2. Desglose Funcional de Módulos (Panel de Control 0-24)

### GRUPO A: INTERRUPTORES AUTOMATICOS 24/7 (BOTONES [1] AL [8])

Configuración permanente en SI / ON para sincronización autónoma cada 3 segundos:

- **[1] WOO_STOCK (SI):** Sube el stock con colchón de seguridad (40%) desde el Excel de Dropbox hacia insumaes.cl.
- **[2] WOO_PRECIOS (SI):** Actualiza los precios con IVA desde el Excel maestro hacia WooCommerce.
- **[3] MODO TURBO DELTA (SI):** Monitorea el Excel en Dropbox cada 3 segundos e inyecta únicamente las diferencias.
- **[4] AUDITOR MELI (SI):** Actualiza automáticamente el archivo AUDITORIA_MELI_INSUMAES.xlsx en Dropbox.
- **[5] MELI_STOCK (SI):** Sincroniza el 40% de la bodega en las 782 publicaciones de Mercado Libre y pausa agotados.
- **[6] MELI_PRECIOS (BLOQUEADO - NO):** Candado permanente para proteger la estructura de precios de Mercado Libre.
- **[7] PORCENTAJE COLCHON (40%):** Define el porcentaje del stock físico que se expone en canales digitales.
- **[8] CORTAFUEGOS PRECIOS (ON 40%):** Bloquea caídas de precio mayores al 40% por errores de digitación en el Excel.

### GRUPO B: RADARES EN VIVO Y OPERACION DIARIA ([9], [12], [14], [15], [17] AL [20])

Herramientas de telemetría en tiempo real y control de inventario de mostrador:

- **[9] MODO PRUEBA (PILOTO):** Entorno de pruebas para validar cambios en 1 producto antes de la ejecución masiva.
- **[12] VER BITACORA DE CAMBIOS:** Historial detallado de movimientos del día (Valor Anterior -> Valor Nuevo).
- **[14] EJECUTAR SINCRONIZACION AHORA:** Fuerza un ciclo completo de lectura e inyección de manera inmediata.
- **[15] ENVIAR REPORTE GMAIL:** Despacha el reporte ejecutivo y planillas de auditoría por correo electrónico.
- **[17] AUDITOR COMPARADOR (WOO vs ML):** Cruza lado a lado Stock, Precios y SKUs entre Bodega, Web y Mercado Libre.
- **[18] RADAR PANTALLA COMPLETA:** Telemetría en vivo de los últimos 30 impactos con marca de tiempo (DD-MM HH:MM:SS).
- **[19] PISTOLA BARRAS & VENTAS MELI:** Descuenta ventas de mostrador o de Mercado Libre directamente sobre el inventario.
- **[20] MONITOR ACTIVADOS Y AGOTADOS:** Filtra productos reactivados (0 -> con stock) y productos agotados en la jornada.

### GRUPO C: RESCATE DE LA NUBE, BACKUPS Y GITHUB ([10], [11], [13], [16] Y [21])

Sistema de respaldo integral de código fuente, bases de datos y estados de inventario:

- **[10] GUARDAR FOTO DE SEGURIDAD MELI:** Almacena una instantánea exacta del stock de las 782 publicaciones de Mercado Libre.
- **[11] RESTAURAR STOCK ORIGINAL MELI:** Revierte las 782 publicaciones al estado registrado en el punto [10].
- **[13] ENVIAR SISTEMA (.ZIP) A DROPBOX:** Empaqueta todos los archivos .py, .sh, .json, .log y .db en BACKUP_ERP_INSUMAES.zip.
- **[16] EXPORTAR CODIGO/LOGS (.TXT):** Genera y sube /RADIOGRAFIA_ERP_INSUMAES.txt a la raíz de Dropbox.
- **[21] SINCRONIZAR CODIGO CON GITHUB:** Versiona y publica los módulos .py, .sh y el manual README.md en GitHub.

### GRUPO D: BOTON [22] — SUITE MAESTRA DE CATALOGO WEB (INSUMAES.CL)

Automatización de fichas técnicas HTML/CSS, estandarización de imágenes y arquitectura de categorías:

- **[22 -> 1] Estandarizador Inteligente de Fotos:** Recorta espacio vacío y encuadra imágenes a 800x720 px por ID, Categoría o Web completa.
- **[22 -> 2] Auto-Linker de Venta Cruzada:** Conecta bidireccionalmente Portaherramientas, Insertos y Accesorios en las fichas técnicas.
- **[22 -> 3] Editor de Textos HTML por Lote:** Busca y reemplaza especificaciones o inyecta notas técnicas en múltiples IDs simultáneamente.
- **[22 -> 4] Constructor Interactivo de Categorías:** Despliega el árbol jerárquico de categorías de WooCommerce y permite crear nuevas.
- **[22 -> 5] Reasignador Definitivo de Categorías:** Traslada lotes de productos (SKU1 | SKU2 | ID) hacia una categoría destino.
- **[22 -> 6] Extracción Maestra Web a Dropbox (.TXT):** Respalda las 1.727 fichas HTML y CSS en /RADIOGRAFIA_CATALOGO_HTML_WOO.txt.
- **[22 -> 7] Restaurador de Seguridad (Ctrl+Z):** Restaura el código HTML o la imagen original de cualquier producto desde la bóveda local.

### GRUPO E: BOTON [23] — CRM NACIONAL (204 CIUDADES) & COTIZACIONES B2B

Motor de inteligencia comercial SQLite en modo 100% Solo Lectura (sin alterar los archivos Excel originales):

- **[23 -> 1] Sincronizar Cotizaciones y Plantilla:** Repara fórmulas J15:J18 en la plantilla oficial e indexa las carpetas mensuales de /COTIZACIONES INSUMAES (445 cotizaciones).
- **[23 -> 2] Unificador Nacional de Clientes y Cobranza:** Lee en modo Solo Lectura los ~204 archivos 'Libro de Clientes [Ciudad].xlsx', 'Cuentas por Cobrar.xlsx' (149 filas) y 'Base-datos-clientes.xlsx' (499 filas), generando /CRM_MAESTRO_NACIONAL_INSUMAES.xlsx.
- **[23 -> 3] Super-Buscador 360° (SQL):** Consulta en 0,01 segundos cualquier Maestranza, RUT, Ciudad o Producto cruzando cartera histórica, cuentas por cobrar y cotizaciones.

---

## 3. Comandos Directos de Ejecución en Terminal (SSH)

- **Abrir Panel Principal:** `python3 ~/panel.py`
- **Abrir Manual de Operaciones:** `python3 ~/manual_cloud.py`
- **Ejecutar Rescate Completo a Dropbox (`.TXT` y `.ZIP`):** `python3 -u ~/rescatar_todo_nube.py`
- **Abrir Suite Maestra Web (`[22]`):** `python3 ~/suite_cloud_woo.py`
- **Abrir CRM Nacional y Cotizaciones B2B (`[23]`):** `python3 ~/centro_cotizaciones.py`
