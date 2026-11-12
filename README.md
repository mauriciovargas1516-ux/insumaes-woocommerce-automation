# ERP Omnicanal Insumaes Cloud — Arquitectura y Manual de Operaciones (V5)

> **Última actualización:** `2026-11-12 16:59:52` (Chile) | **38 Funciones Activas (Panel 0-26)** | **Stack:** Python, Google Cloud VM, SQLite, WooCommerce API, Mercado Libre API, Dropbox API

---

## 1. Impacto Operativo y Porcentaje de Mejora (Trabajo Manual vs. Arquitectura Cloud)

**Acceso Rápido (Protegido por Login Google IAM):** [Abrir Consola SSH en Google Cloud (vm-insumaes)](https://ssh.cloud.google.com/v2/ssh/projects/motor-sii-python/zones/us-central1-a/instances/vm-insumaes)

El sistema transforma procesos manuales repetitivos en operaciones automatizadas por lote en Google Cloud, logrando una **mejora de eficiencia del 95,3%** (**21,2 veces más rápido**), con **52,5 horas ahorradas al mes** y **630,0 horas ahorradas al año** (**75,0 jornadas laborales completas**):

| Proceso Operativo / Comercial | Volumen Activo | Manual vs. Cloud | Ahorro (Mes / Año) | % Mejora (Velocidad) |
| :--- | :--- | :---: | :---: | :---: |
| **1. Sincronización Stock y Precios (Woo + ML)** | 2.509 ítems (550 cambios/mes) | 23,8 hrs vs. **0,9 hrs** | **22,9 hrs/mes** (274,8 hrs/año) | **96,2% (26,4x más rápido)** |
| **2. Emisión y Cruce de Cotizaciones B2B** | 141 cot/mes (445 en SQL) | 18,8 hrs vs. **1,2 hrs** | **17,6 hrs/mes** (211,2 hrs/año) | **93,6% (15,7x más rápido)** |
| **3. Estandarización HTML/CSS y Auto-Linker ISO** | 752 fichas vinculadas | 7,5 hrs vs. **0,2 hrs** | **7,3 hrs/mes** (87,6 hrs/año) | **97,3% (37,5x más rápido)** |
| **4. Estandarización de Fotos (800x720) y Categorías** | 1.727 prods (100 ajustes/mes) | 5,0 hrs vs. **0,3 hrs** | **4,7 hrs/mes** (56,4 hrs/año) | **94,0% (16,7x más rápido)** |
| **TOTAL OPERACIÓN CONTINUA** | **2.509 ítems + CRM B2B** | **55,1 hrs vs. 2,6 hrs** | **52,5 hrs/mes (630,0 hrs/año)** | **95,3% (21,2x más rápido)** |

### Porcentaje de Mejora en Tareas Masivas por Lote (Ejecución Puntual)

| Tarea Masiva de Catálogo o Inteligencia Comercial | Tiempo Manual | Tiempo Cloud | Horas Ahorradas | % Mejora (Multiplicador) |
| :--- | :---: | :---: | :---: | :---: |
| **Conectar botones de venta cruzada en 752 productos web** | 43,9 horas (5,2 días) | **4,0 minutos** | 43,8 horas | **99,8% (658,5x más rápido)** |
| **Unificar ~204 Libros de Clientes por Ciudad + Cuentas por Cobrar** | 18,0 horas (2,1 días) | **1,8 minutos** | 17,9 horas | **99,8% (600,0x más rápido)** |
| **Buscar historial, RUT y cotizaciones de un cliente en 204 ciudades** | 15,0 minutos | **0,01 segundos (SQL)** | 15,0 minutos | **99,9% (90.000x más rápido)** |
| **Preparar y estructurar las 1.727 fichas para 1 nuevo Marketplace** | 172,7 horas (20,6 días) | **0,5 horas (30 min)** | 172,2 horas | **99,7% (345,4x más rápido)** |
| **Expandir catálogo a 3 nuevos Marketplaces (Falabella, Paris, Lider)** | 518,1 horas (61,7 días) | **1,5 horas** | 516,6 horas | **99,7% (345,4x más rápido)** |

---

## 2. Desglose Funcional de Módulos (Panel de Control 0-25)

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

### GRUPO D: BOTONES [22] Y [25] — SUITE DE CATALOGO WEB Y PRECIOS POR %

Automatización de fichas técnicas HTML/CSS, estandarización de imágenes y arquitectura de categorías:

- **[22 -> 1] Estandarizador Inteligente de Fotos:** Recorta espacio vacío y encuadra imágenes a 800x720 px por ID, Categoría o Web completa.
- **[22 -> 2] Auto-Linker de Venta Cruzada:** Conecta bidireccionalmente Portaherramientas, Insertos y Accesorios en las fichas técnicas.
- **[22 -> 3] Editor de Textos HTML por Lote:** Busca y reemplaza especificaciones o inyecta notas técnicas en múltiples IDs simultáneamente.
- **[22 -> 4] Constructor Interactivo de Categorías:** Despliega el árbol jerárquico de categorías de WooCommerce y permite crear nuevas.
- **[22 -> 5] Reasignador Definitivo de Categorías:** Traslada lotes de productos (SKU1 | SKU2 | ID) hacia una categoría destino.
- **[22 -> 6] Extracción Maestra Web a Dropbox (.TXT):** Respalda las 1.727 fichas HTML y CSS en /RADIOGRAFIA_CATALOGO_HTML_WOO.txt.
- **[22 -> 7] Restaurador de Seguridad (Ctrl+Z):** Restaura el código HTML o la imagen original de cualquier producto desde la bóveda local.
- **[25] Ajustador Masivo de Precios por % y Ofertas Tachadas:** Permite aplicar aumentos o descuentos porcentuales (+X% / -X%) o activar precios de oferta tachados por Categoría o Lote con redondeo a $100 y reversión instantánea (Ctrl+Z).

### GRUPO E: BOTON [23] — CRM NACIONAL (204 CIUDADES) & COTIZACIONES B2B

Motor de inteligencia comercial SQLite en modo 100% Solo Lectura (sin alterar los archivos Excel originales):

- **[23 -> 1] Sincronizar Cotizaciones y Plantilla:** Valida automáticamente la integridad de fórmulas de subtotales/IVA e indexa las carpetas mensuales de /COTIZACIONES INSUMAES en SQLite.
- **[23 -> 2] Unificador Nacional de Clientes y Cobranza:** Lee en modo Solo Lectura los ~204 archivos 'Libro de Clientes [Ciudad].xlsx', 'Cuentas por Cobrar.xlsx' (149 filas) y 'Base-datos-clientes.xlsx' (499 filas), generando /CRM_MAESTRO_NACIONAL_INSUMAES.xlsx.
- **[23 -> 3] Super-Buscador 360° (SQL):** Consulta en 0,01 segundos cualquier Maestranza, RUT, Ciudad o Producto cruzando cartera histórica, cuentas por cobrar y cotizaciones.

---

## 3. Comandos Directos de Ejecución en Terminal (SSH)

- **Abrir Panel Principal:** `python3 ~/panel.py`
- **Abrir Manual de Operaciones:** `python3 ~/manual_cloud.py`
- **Ejecutar Rescate Completo a Dropbox (`.TXT` y `.ZIP`):** `python3 -u ~/rescatar_todo_nube.py`
- **Abrir Suite Maestra Web (`[22]`):** `python3 ~/suite_cloud_woo.py`
- **Abrir CRM Nacional y Cotizaciones B2B (`[23]`):** `python3 ~/centro_cotizaciones.py`
- **Abrir Esqueleto Integrador y Detector de Brechas (`[26]`):** `python3 ~/esqueleto_integrador.py`

---

## 4. Arquitectura de Archivos del Repositorio (Índice de Módulos por Capa)

Para mantener importación directa en tiempo real con el demonio activo en RAM, los módulos residen en la raíz organizados en **5 capas de ingeniería**:

| Capa del Sistema | Archivos `.py` / `.sh` Principales | Rol Técnico dentro del Ecosistema |
| :--- | :--- | :--- |
| **1. Núcleo y Panel Central** | `panel.py`, `lanzar_todo.sh`, `lee_config.py`, `manual_cloud.py` | Interfaz de control (Botones `0` a `26`), configuración en vivo y documentación automática. |
| **2. Motor Delta 24/7 y Reglas** | `marcha_rapida_delta.py`, `motor_insumaes.py`, `reglas_precision.py`, `radar_vivo.py`, `monitor_detenidas.py` | Sincronización cada 3s, colchón 40%, cortafuegos de precios, cajas de 10 insertos y reactivación. |
| **3. Suite WooCommerce (Web)** | `suite_cloud_woo.py`, `autolinker_web.py`, `estandarizador_fotos_woo.py`, `ajustador_precios_woo.py`, `exportar_html_woo.py` | Venta cruzada ISO (752 fichas), fotos `800x720 px`, categorías y ajuste masivo de precios por `%`. |
| **4. Suite Mercado Libre & POS** | `auditor_meli.py`, `nivelar_meli_vivo.py`, `post_meli.py`, `comparador_omnicanal.py`, `pistola_pos.py`, `generador_carta_ean.py` | Sincronización de 782 publicaciones ML, laboratorio piloto, pistola láser POS y códigos de barra. |
| **5. CRM SQLite, B2B y Rescate** | `centro_cotizaciones.py`, `esqueleto_integrador.py`, `rescatar_todo_nube.py`, `vigia_github.py`, `.env.example` | SQLite (445 cotizaciones + ~204 ciudades + Cuentas por Cobrar en Solo Lectura), brechas y backups. |
