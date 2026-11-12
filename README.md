# ERP Omnicanal Insumaes Cloud — Arquitectura y Manual de Operaciones (V6)

> **Última actualización:** `2026-11-12 18:15:56` (Chile) | **41 Funciones Activas (Panel 0-26)** | **Stack:** Python, Google Cloud VM, SQLite, WooCommerce API, Mercado Libre API, Dropbox API

---

## 1. Impacto Operativo y Porcentaje de Mejora (Trabajo Manual vs. Arquitectura Cloud)

**Acceso Rápido (Protegido por Login Google IAM):** [Abrir Consola SSH en Google Cloud (vm-insumaes)](https://ssh.cloud.google.com/v2/ssh/projects/motor-sii-python/zones/us-central1-a/instances/vm-insumaes)

El sistema transforma procesos manuales repetitivos en operaciones automatizadas por lote en Google Cloud, logrando una **mejora de eficiencia del 95,3%** (**21,2 veces más rápido**), con **52,5 horas ahorradas al mes** y **630,0 horas ahorradas al año** (**75,0 jornadas laborales completas** de 8,4 horas):

| Proceso Operativo / Comercial | Volumen Activo | Manual vs. Cloud | Ahorro (Mes / Año) | % Mejora (Velocidad) |
| :--- | :--- | :---: | :---: | :---: |
| **1. Sincronización Stock y Precios (Woo + ML)** | 2.509 ítems (550 cambios/mes) | 23,8 hrs vs. **0,9 hrs** | **22,9 hrs/mes** (274,8 hrs/año) | **96,2% (26,4x más rápido)** |
| **2. Emisión y Cruce de Cotizaciones B2B** | 141 cot/mes (445 en SQL) | 18,8 hrs vs. **1,2 hrs** | **17,6 hrs/mes** (211,2 hrs/año) | **93,6% (15,7x más rápido)** |
| **3. Estandarización HTML/CSS y Auto-Linker ISO** | 752 fichas vinculadas | 7,5 hrs vs. **0,2 hrs** | **7,3 hrs/mes** (87,6 hrs/año) | **97,3% (37,5x más rápido)** |
| **4. Estandarización de Fotos (800x720) y Categorías** | 1.727 prods (100 ajustes/mes) | 5,0 hrs vs. **0,3 hrs** | **4,7 hrs/mes** (56,4 hrs/año) | **94,0% (16,7x más rápido)** |
| **TOTAL OPERACIÓN CONTINUA** | **2.509 ítems + CRM B2B** | **55,1 hrs vs. 2,6 hrs** | **52,5 hrs/mes (630,0 hrs/año)** | **95,3% (21,2x más rápido)** |

### Porcentaje de Mejora en Tareas Masivas por Lote y Expansión Omnicanal

| Tarea Masiva de Catálogo o Inteligencia Comercial | Tiempo Manual | Tiempo Cloud | Horas Ahorradas | % Mejora (Multiplicador) |
| :--- | :---: | :---: | :---: | :---: |
| **Conectar botones de venta cruzada en 752 productos web** | 43,9 horas (5,2 días) | **4,0 minutos** | 43,8 horas | **99,8% (658,5x más rápido)** |
| **Unificar ~204 Libros de Clientes por Ciudad + Cuentas por Cobrar** | 18,0 horas (2,1 días) | **1,8 minutos** | 17,9 horas | **99,8% (600,0x más rápido)** |
| **Buscar historial, RUT y cotizaciones de un cliente en 204 ciudades** | 15,0 minutos | **0,01 segundos (SQL)** | 15,0 minutos | **99,9% (90.000x más rápido)** |
| **Auditar diferencias de precio y margen líquido en 782 ítems ML vs. Web** | 19,5 horas (2,3 días) | **3,0 segundos** | 19,5 horas | **99,9% (23.400x más rápido)** |
| **Preparar y estructurar las 1.727 fichas para 1 nuevo Marketplace** | 172,7 horas (20,6 días) | **0,5 horas (30 min)** | 172,2 horas | **99,7% (345,4x más rápido)** |
| **Implementación 'Llave en Mano' desde cero (Tienda Woo + ML + ERP Cloud)** | 120,0 horas (14,3 días) | **5,5 horas (1 jornada)** | 114,5 horas | **95,4% (21,8x más rápido)** |

### Arquitectura de Traspasabilidad Ultra-Rápida Entre Canales (El 'Trampolín Omnicanal')

Una vez que el catálogo vive estructurado en la Bóveda Maestra del servidor (`1.727` productos totales; `1.500` con stock positivo, precio y fotografía listos), el motor actúa como un **traductor universal de comercio electrónico** capaz de migrar todo el inventario de un canal a otro en **segundos**, aplicando automáticamente las reglas técnicas, de empaque y de comisión de cada plataforma:

| Canal de Destino | Productos Listos | Regla de Transformación Automática | Tiempo Manual | Tiempo Cloud |
| :--- | :---: | :--- | :---: | :---: |
| **1. Mercado Libre (`Pestaña 1`)** | 1.376 packs/ítems | Títulos `<=60` car., texto plano sin HTML, convierte insertos a **Cajas x10 uds** y aplica recargo comercial (`+25%`). | 150,0 hrs | **0,4 min** |
| **2. Falabella / Paris / Lider (`Pestaña 2`)** | 1.500 productos | Estructura `Seller_SKU`, precio normal y oferta con cobertura de comisión/envío y descripción limpia. | 450,0 hrs (3 canales) | **1,0 min** |
| **3. Shopify / Nuevo Portal B2B (`Pestaña 3`)** | 1.500 productos | Genera `Handle` SEO, conserva **100% del HTML + CSS y botones de venta cruzada** y enlaza galerías de fotos. | 150,0 hrs | **0,4 min** |
| **TOTAL MULTICANAL (5 PLATAFORMAS)** | **1.500 SKUs activos** | **Sincronización simultánea de stock cada 3 segundos post-migración** | **772,7 hrs (91,7 días)** | **2,3 hrs (99,7% ahorro)** |

---

## 2. Desglose Funcional de Módulos (Panel de Control 0-26)

### GRUPO A: INTERRUPTORES AUTOMATICOS 24/7 Y REGLAS DE PRECISION (BOTONES [1] AL [8])

Configuración permanente en SI / ON para sincronización autónoma cada 3 segundos:

- **[1] WOO_STOCK (SI):** Sube el stock con colchón de seguridad (40%) desde el Excel de Dropbox hacia insumaes.cl.
- **[2] WOO_PRECIOS (SI):** Actualiza los precios con IVA desde el Excel maestro hacia WooCommerce.
- **[3] MODO TURBO DELTA (SI):** Monitorea el Excel en Dropbox cada 3 segundos en memoria RAM e inyecta únicamente las diferencias en 0,35 a 1,08 segundos.
- **[4] AUDITOR MELI (SI):** Actualiza automáticamente el archivo AUDITORIA_MELI_INSUMAES.xlsx en Dropbox.
- **[5] MELI_STOCK (SI) + Regla de Paquetes (Cajas de 10 y Multipacks):** Sincroniza el 40% de la bodega en las 782 publicaciones de Mercado Libre, armando cajas cerradas (ej. cajas de 10 insertos o packs de 5 brocas) y deteniendo automáticamente la publicación en Mercado Libre si el stock baja del mínimo del paquete (protegiendo el 42,6% del catálogo de insertos — 124 de 291 modelos equivalentes a $20.886.080 CLP — mientras mantiene la venta unitaria activa en insumaes.cl).
- **[6] MELI_PRECIOS (BLOQUEADO - NO):** Candado permanente para proteger la estructura de precios de Mercado Libre (compensación de comisión del 14% al 19% más costo de Mercado Envíos).
- **[7] PORCENTAJE COLCHON (40%):** Define el porcentaje del stock físico que se expone en canales digitales.
- **[8] CORTAFUEGOS PRECIOS (ON 40%):** Bloquea en 0,01 segundos variaciones bruscas de precio mayores al 40% por errores de digitación en el Excel.

### GRUPO B: RADARES EN VIVO Y OPERACION DIARIA ([9], [12], [14], [15], [17] AL [20])

Herramientas de telemetría en tiempo real y control de inventario de mostrador:

- **[9] MODO PRUEBA (PILOTO):** Entorno de pruebas para validar cambios en 1 producto antes de la ejecución masiva.
- **[12] VER BITACORA DE CAMBIOS:** Historial detallado de movimientos del día (Valor Anterior -> Valor Nuevo).
- **[14] EJECUTAR SINCRONIZACION AHORA:** Fuerza un ciclo completo de lectura e inyección de manera inmediata.
- **[15] ENVIAR REPORTE GMAIL:** Despacha el reporte ejecutivo y planillas de auditoría por correo electrónico.
- **[17] AUDITOR COMPARADOR (WOO vs ML):** Cruza lado a lado Stock, Precios y SKUs entre Bodega, Web y Mercado Libre.
- **[18] RADAR PANTALLA COMPLETA:** Telemetría en vivo de los últimos 30 impactos con marca de tiempo (DD-MM HH:MM:SS).
- **[19] PISTOLA BARRAS & VENTAS MELI:** Descuenta ventas de mostrador (pistola láser POS) o cruza Ventas ML para descontar directamente sobre el inventario.
- **[20] MONITOR ACTIVADOS Y AGOTADOS:** Filtra productos reactivados automáticamente (0 -> con stock) y productos agotados en la jornada.

### GRUPO C: RESCATE DE LA NUBE, BACKUPS Y GITHUB ([10], [11], [13], [16] Y [21])

Sistema de respaldo integral de código fuente, bases de datos y estados de inventario:

- **[10] GUARDAR FOTO DE SEGURIDAD MELI:** Almacena una instantánea exacta del stock de las 782 publicaciones de Mercado Libre.
- **[11] RESTAURAR STOCK ORIGINAL MELI:** Revierte las 782 publicaciones al estado registrado en el punto [10].
- **[13] ENVIAR SISTEMA (.ZIP) A DROPBOX:** Empaqueta todos los archivos .py, .sh, .json, .log y .db en BACKUP_ERP_INSUMAES.zip.
- **[16] EXPORTAR CODIGO/LOGS (.TXT):** Genera y sube /RADIOGRAFIA_ERP_INSUMAES.txt a la raíz de Dropbox.
- **[21] SINCRONIZAR CODIGO CON GITHUB:** Versiona y publica los módulos .py, .sh, .env.example y el manual README.md en GitHub.

### GRUPO D: BOTONES [22] Y [25] — SUITE DE CATALOGO WEB Y AJUSTADOR DE PRECIOS POR %

Automatización de fichas técnicas HTML/CSS, estandarización de imágenes, categorías y gestión masiva de precios:

- **[22 -> 1] Estandarizador Inteligente de Fotos:** Recorta espacio vacío superior y encuadra imágenes a 800x720 px por ID, Categoría o Web completa.
- **[22 -> 2] Auto-Linker de Venta Cruzada ISO:** Conecta bidireccionalmente Portaherramientas, Insertos y Accesorios en 752 fichas técnicas.
- **[22 -> 3] Editor de Textos HTML por Lote:** Busca y reemplaza especificaciones o inyecta notas técnicas en múltiples IDs simultáneamente.
- **[22 -> 4] Constructor Interactivo de Categorías:** Despliega el árbol jerárquico de categorías de WooCommerce y permite crear nuevas.
- **[22 -> 5] Reasignador Definitivo de Categorías:** Traslada lotes de productos (SKU1 | SKU2 | ID) hacia una categoría destino.
- **[22 -> 6] Extracción Maestra Web a Dropbox (.TXT):** Respalda las 1.727 fichas HTML y CSS en /RADIOGRAFIA_CATALOGO_HTML_WOO.txt.
- **[22 -> 7] Restaurador de Seguridad (Ctrl+Z):** Restaura el código HTML o la imagen original de cualquier producto desde la bóveda local.
- **[25] Ajustador Masivo de Precios por % y Ofertas Tachadas:** Permite aplicar aumentos o descuentos porcentuales (+X% / -X%) sobre $194.712.264 CLP en las 6 categorías principales (1.013 productos) o activar precios de oferta tachados (sale_price) con redondeo comercial a $100 y reversión instantánea (Ctrl+Z).

### GRUPO E: BOTONES [23] Y [26] — CRM NACIONAL (204 CIUDADES), COTIZACIONES & ESQUELETO OMNICANAL

Motor de inteligencia comercial SQLite en modo 100% Solo Lectura, expansión omnicanal y auditoría de márgenes:

- **[23 -> 1] Sincronizar Cotizaciones y Plantilla:** Valida automáticamente la integridad de fórmulas de subtotales/IVA e indexa las carpetas mensuales de /COTIZACIONES INSUMAES en SQLite (445 cotizaciones B2B).
- **[23 -> 2] Unificador Nacional de Clientes y Cobranza:** Lee en modo 100% Solo Lectura los ~204 archivos 'Libro de Clientes [Ciudad].xlsx', 'Cuentas por Cobrar.xlsx' (149 filas) y 'Base-datos-clientes.xlsx' (499 filas), generando /CRM_MAESTRO_NACIONAL_INSUMAES.xlsx.
- **[23 -> 3] Super-Buscador 360° (SQL):** Consulta en 0,01 segundos cualquier Maestranza, RUT, Ciudad o Producto cruzando cartera histórica, cuentas por cobrar y cotizaciones.
- **[26 -> 1] Escáner de Brechas Omnicanal (WooCommerce -> Mercado Libre):** Identifica los 718 productos que cuentan con stock positivo, precio y fotografía en insumaes.cl pero aún no están publicados en Mercado Libre (más los 95 productos con stock pero sin foto), exportando /BRECHA_EXPANSION_WOO_A_MELI.xlsx con texto plano y precio sugerido (+18%).
- **[26 -> 2] Generador de Kit 'Llave en Mano' para Clientes Nuevos:** Crea el molde limpio .env.example y la planilla auto-ajustada /PLANTILLA_ONBOARDING_CLIENTE_NUEVO.xlsx para replicar el ecosistema en otras empresas.
- **[26 -> 4] Traspasador Universal Multi-Canal (Trampolín a Mercado Libre, Falabella, Paris, Lider y Shopify):** Transforma en un solo clic los 1.500 productos con stock y foto de la bóveda web hacia los formatos de carga masiva de Mercado Libre (respetando la regla de cajas de 10 insertos), Falabella/Paris/Lider y Shopify/B2B con recargo porcentual configurable en /TRASPASO_MULTICANAL_UNIVERSAL.xlsx.
- **[26 -> 3] Auditor de Diferencia de Precios y Margen Líquido (ML vs. Web — 100% Solo Lectura):** Cruza las 782 publicaciones de Mercado Libre contra el Excel/Web sin modificar ningún precio en ML, calculando comisión, envío estimado, ingreso líquido y semáforo de rentabilidad (<20% Alerta Margen Bajo, 20%-45% Margen Sano, >45% Sobreprecio Alto) más las 14 publicaciones sin pareja en Excel en /DIFERENCIA_PRECIOS_ML_VS_WEB.xlsx.
- **Auto-Formateador Ejecutivo de Planillas (formateador_excel_cloud.py):** Ajusta automáticamente anchos de columna (14 a 58 caracteres), altos de fila (30 pt en títulos y 22+ pt en datos), formato moneda '$' y autofiltros en todos los reportes Excel exportados a Dropbox.

---

## 3. Comandos Directos de Ejecución en Terminal (SSH)

- **Abrir Panel Principal (Botones 0-26):** `python3 ~/panel.py`
- **Abrir Manual de Operaciones (`[24]`):** `python3 ~/manual_cloud.py`
- **Ejecutar Rescate Completo a Dropbox (`.TXT` y `.ZIP`):** `python3 -u ~/rescatar_todo_nube.py`
- **Abrir Suite Maestra Web (`[22]`):** `python3 ~/suite_cloud_woo.py`
- **Abrir CRM Nacional y Cotizaciones B2B (`[23]`):** `python3 ~/centro_cotizaciones.py`
- **Abrir Ajustador Masivo de Precios por % (`[25]`):** `python3 ~/ajustador_precios_woo.py`
- **Abrir Esqueleto Integrador, Brechas y Auditor de Precios ML (`[26]`):** `python3 ~/esqueleto_integrador.py`

---

## 4. Arquitectura de Archivos del Repositorio (Índice de Módulos por Capa)

Para mantener importación directa en tiempo real con el demonio activo en RAM (`PID Activo`), los módulos residen en el directorio raíz organizados en **5 capas de ingeniería**:

| Capa del Sistema | Archivos `.py` / `.sh` Principales | Rol Técnico dentro del Ecosistema |
| :--- | :--- | :--- |
| **1. Núcleo y Panel Central** | `panel.py`, `lanzar_todo.sh`, `lee_config.py`, `manual_cloud.py` | Interfaz de control (Botones `0` a `26` — 40 funciones activas), configuración en vivo y documentación automática. |
| **2. Motor Delta 24/7 y Reglas** | `marcha_rapida_delta.py`, `motor_insumaes.py`, `reglas_precision.py`, `radar_vivo.py`, `monitor_detenidas.py` | Sincronización cada 3s, colchón 40%, cortafuegos de precios (0,01s), armado/freno de cajas de 10 insertos y reactivación. |
| **3. Suite WooCommerce (Web)** | `suite_cloud_woo.py`, `autolinker_web.py`, `estandarizador_fotos_woo.py`, `ajustador_precios_woo.py`, `exportar_html_woo.py` | Venta cruzada ISO (752 fichas), fotos `800x720 px`, categorías y ajuste masivo de precios por `%` con ofertas tachadas. |
| **4. Suite Mercado Libre & POS** | `auditor_meli.py`, `nivelar_meli_vivo.py`, `post_meli.py`, `comparador_omnicanal.py`, `pistola_pos.py`, `generador_carta_ean.py` | Sincronización de 782 publicaciones ML, laboratorio piloto, pistola láser POS y pliegos PDF de códigos de barra. |
| **5. CRM SQLite, B2B y Expansión** | `centro_cotizaciones.py`, `esqueleto_integrador.py`, `formateador_excel_cloud.py`, `rescatar_todo_nube.py`, `.env.example` | SQLite (445 cotizaciones + ~204 ciudades + Cuentas por Cobrar en Solo Lectura), detector de brechas, auditoría de precios ML y backups. |
