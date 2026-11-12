# 🛠️ ERP Omnicanal Insumaes Cloud — Manual Oficial de Operaciones (V5)

> **Última actualización:** `2026-11-11 21:19:41` (Chile) | **35 Funciones Activas (Panel 0-24)**

---

## 🟢 GRUPO A: INTERRUPTORES AUTOMÁTICOS 24/7 (BOTONES [1] AL [8])

```text
Los dejas en SI / ON una sola vez y el vigilante trabaja solo cada 3 segundos:
 • [1] WOO_STOCK (SI)        : Sube el stock con colchón (40%) del Excel a insumaes.cl.
 • [2] WOO_PRECIOS (SI)      : Sube los precios con IVA del Excel a tu web automáticamente.
 • [3] MODO TURBO DELTA (SI) : Vigila tu Excel en Dropbox cada 3 seg e inyecta solo cambios.
 • [4] AUDITOR MELI (SI)     : Actualiza AUDITORIA_MELI_INSUMAES.xlsx en tu Dropbox.
 • [5] MELI_STOCK (SI)       : Sube el 40% de tu bodega a las 782 publicaciones de Mercado Libre.
 • [6] MELI_PRECIOS (BLOQ)   : Candado fijo (NO) para proteger tus precios de Mercado Libre.
 • [7] PORCENTAJE COLCHÓN    : Define qué % de la bodega se publica en internet (ej: 40%).
 • [8] CORTAFUEGOS PRECIOS   : Bloquea caídas bruscas > 40% si alguien digita mal en Excel.
```

## 🔭 GRUPO B: RADARES EN VIVO Y OPERACIÓN DIARIA ([9], [12], [14], [15], [17] AL [20])

```text
Para supervisar en tiempo real o descontar ventas de mostrador:
 • [9]  MODO PRUEBA (PILOTO) : Laboratorio para probar 1 producto antes del lote completo.
 • [12] VER BITÁCORA         : Historial de qué productos cambiaron hoy (Antes -> Ahora).
 • [14] EJECUTAR AHORA       : Fuerza una sincronización completa en este mismo segundo.
 • [15] ENVIAR REPORTE GMAIL : Envía el resumen y Excels de auditoría a tu correo.
 • [17] AUDITOR COMPARADOR   : Compara lado a lado Stock y Precios (Excel vs Web vs ML).
 • [18] RADAR PANTALLA COMPL.: Últimos 30 impactos en vivo con fecha (DD-MM HH:MM:SS).
 • [19] PISTOLA BARRAS & ML  : Descuenta ventas de mesón (pistola) o de ML en el Excel.
 • [20] MONITOR ACTIVADOS    : Muestra qué revivió (0 -> Stock) y qué se agotó hoy (0 uds).
```

## 🛡️ GRUPO C: RESCATE DE LA NUBE, BACKUPS Y GITHUB ([10], [11], [13], [16] Y [21])

```text
Tus seguros de vida para respaldar código, logs, bases de datos e inventario:
 • [10] GUARDAR FOTO MELI    : Guarda copia exacta del stock de tus 782 ítems de ML.
 • [11] RESTAURAR STOCK MELI : Devuelve tus 782 ítems de ML a la foto guardada en [10].
 • [13] ENVIAR .ZIP A DROPBOX: Guarda todos tus .py, .sh, .json, .log y .db en Dropbox (.ZIP).
 • [16] EXPORTAR CÓDIGO .TXT : Sube /RADIOGRAFIA_ERP_INSUMAES.txt a la raíz de tu Dropbox.
 • [21] SINCRONIZAR GITHUB   : Sube todos tus .py, .sh y el Manual README.md a tu GitHub.
```

## 🛠️ GRUPO D: BOTÓN [22] — SUITE MAESTRA DE CATÁLOGO WEB (INSUMAES.CL)

```text
Taller de diseño, fotos, categorías y botones de venta cruzada en WooCommerce:
 • [22 -> 1] 📸 Estandarizador Fotos : Encuadra fotos gigantes a 800x720 px por ID, Categoría o Web.
 • [22 -> 2] 🔗 Auto-Linker Botones  : Conecta Portas <-> Insertos en las Cajas Amarillas.
 • [22 -> 3] ✏️  Editor HTML por Lote : Busca/reemplaza textos o agrega notas en varios IDs.
 • [22 -> 4] 🏗️  Constructor Categor. : Dibuja el árbol de categorías de insumaes.cl y crea nuevas.
 • [22 -> 5] 🚚 Reasignador Categor. : Mueve lotes de productos (SKU1 | SKU2) de categoría.
 • [22 -> 6] 💾 Extracción Web (.TXT): Respalda las 1.727 fichas HTML en /RADIOGRAFIA_CATALOGO_HTML_WOO.txt.
 • [22 -> 7] ⏪ Restaurador (Ctrl+Z) : Devuelve el HTML o la Foto de 1 ID (o todos) al original.
```

## 🏢 GRUPO E: BOTÓN [23] — CRM NACIONAL (204 CIUDADES) & COTIZACIONES B2B

```text
Inteligencia comercial en MODO 100% SOLO LECTURA (jamás modifica los Excels de tu tío):
 • [23 -> 1] 🔧 Sincronizar Cotizac. : Repara fórmulas J15:J18 en Plantilla e indexa /COTIZACIONES INSUMAES.
 • [23 -> 2] 🌎 Unificar 204 Ciudades: Lee los ~204 'Libro de Clientes [Ciudad].xlsx' + 'Cuentas por Cobrar.xlsx'
                                       y crea en Dropbox /CRM_MAESTRO_NACIONAL_INSUMAES.xlsx.
 • [23 -> 3] 🔎 Super-Buscador 360°  : Busca en 0,01s cualquier Maestranza, RUT, Ciudad o Producto.
```

## ⚡ Comandos Directos en Terminal SSH
- Panel Principal: `python3 ~/panel.py`
- Manual Interactivo: `python3 ~/manual_cloud.py`
- Rescatar Todo a Dropbox (`.TXT` y `.ZIP`): `python3 -u ~/rescatar_todo_nube.py`
