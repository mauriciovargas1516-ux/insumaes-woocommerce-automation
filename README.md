#  Sincronizador Automático de Inventario (Python & GCP)

Pipeline autónomo diseñado para auditar, sincronizar y respaldar el inventario físico de una tienda local con su plataforma e-commerce (WooCommerce), eliminando el error humano y optimizando las operaciones comerciales.

##  Funcionalidades Clave
* **Auditoría de Datos:** Extracción y análisis de más de 1.500 productos en tiempo real mediante la API de WooCommerce.
* **Cazador de Duplicados:** Algoritmo dedicado a identificar inconsistencias en la base de datos (nombres clonados, URLs duplicadas).
* **Cortafuegos Comercial:** Lógica de negocio integrada que bloquea la inyección de precios en $0 o varianzas extremas para proteger la rentabilidad.
* **Respaldo en la Nube:** Integración con la API de Dropbox para almacenar reportes de pre-sincronización de forma autónoma.
* **Notificaciones Automatizadas:** Envío de reportes de ejecución por correo electrónico tras cada ciclo.

##  Tecnologías Utilizadas
* **Lenguaje:** Python 3
* **Procesamiento de Datos:** Pandas
* **APIs:** WooCommerce API, Dropbox API
* **Despliegue:** Servidores Linux (Google Cloud Platform) orquestados mediante Bash Scripts (Cron Jobs).
