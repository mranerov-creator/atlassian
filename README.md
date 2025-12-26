# Shadow IT Report - Atlassian

Web estática para presentar informes de Shadow IT de sitios Atlassian Cloud no gestionados.

## Estructura del Proyecto

```
.
├── data/
│   ├── shadow_it_sites.csv    # CSV con datos de sitios shadow IT
│   └── report_data.json       # Datos procesados para la web
├── scripts/
│   └── fetch_atlassian_data.py # Script para extraer datos de APIs
├── web/
│   ├── index.html             # Dashboard principal
│   ├── sites.html             # Lista de sitios
│   ├── site-detail.html       # Detalles de un sitio
│   ├── apps.html              # Apps instaladas
│   ├── css/styles.css         # Estilos
│   └── js/
│       ├── app.js             # Lógica de la aplicación
│       └── data.js            # Datos embebidos
└── README.md
```

## Uso

### Ver el Informe (sin servidor)

Simplemente abre `web/index.html` en tu navegador. Los datos están embebidos en `data.js`.

### Actualizar Datos desde APIs de Atlassian

Para obtener datos detallados (proyectos, espacios, plugins), necesitas credenciales de Atlassian:

1. Crea un API Token en: https://id.atlassian.com/manage-profile/security/api-tokens

2. Ejecuta el script:

```bash
python scripts/fetch_atlassian_data.py \
    --email tu-email@empresa.com \
    --token TU_API_TOKEN \
    --csv data/shadow_it_sites.csv \
    --output data/report_data.json
```

O usando variables de entorno:

```bash
export ATLASSIAN_EMAIL=tu-email@empresa.com
export ATLASSIAN_API_TOKEN=TU_API_TOKEN
python scripts/fetch_atlassian_data.py
```

3. Regenera el archivo de datos embebidos:

```bash
echo "const REPORT_DATA = " > web/js/data.js
cat data/report_data.json >> web/js/data.js
echo ";" >> web/js/data.js
```

### Modo sin API (solo datos del CSV)

Para generar datos de ejemplo basados solo en el CSV:

```bash
python scripts/fetch_atlassian_data.py --skip-api
```

## Datos Extraídos

El script obtiene la siguiente información de cada sitio:

### Jira
- Número de proyectos por tipo (Software, Service Desk, Business)
- Detalles de cada proyecto (nombre, clave, tipo)
- Última actividad (fecha de última actualización de issues)

### Confluence
- Número de espacios
- Detalles de cada espacio (nombre, clave, tipo)
- Última actividad (fecha de última página modificada)

### Apps/Plugins
- Lista de apps del Marketplace instaladas
- Nombre, versión y vendor de cada app

## APIs Utilizadas

- [Jira Cloud REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
  - `GET /rest/api/3/project/search` - Lista de proyectos

- [Confluence Cloud REST API v2](https://developer.atlassian.com/cloud/confluence/rest/v2/)
  - `GET /wiki/api/v2/spaces` - Lista de espacios
  - `GET /wiki/api/v2/pages` - Última actividad

- [UPM REST API](https://developer.atlassian.com/server/framework/upm/)
  - `GET /rest/plugins/1.0/` - Plugins instalados

## Requisitos

- Python 3.8+
- requests (`pip install requests`)
- Navegador web moderno

## Notas de Seguridad

- Los API tokens son sensibles. No los compartas ni los incluyas en el código.
- El script necesita acceso de lectura a los sitios para obtener datos.
- Algunos endpoints (como plugins) requieren permisos de administrador.
