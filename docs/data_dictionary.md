# Diccionario de Datos

Este documento describe la estructura de los archivos `.parquet` generados por el proceso de extracción de GitHub Agentic Workflows.

## 1. Tabla: `repositories.parquet`

Esta tabla almacena la información original de los repositorios procesados y filtrados. Solo contiene repositorios que hacen uso de GH-AW (`uses_gh_aw == True`).

| Columna | Tipo de Dato | Significado | Claves |
|---------|--------------|-------------|--------|
| `repo_id` | String | Identificador único del repositorio en la plataforma (formato: `owner/repo`). Corresponde a la columna `name` del CSV original. | **Primary Key** |
| `uses_gh_aw` | Boolean | Indica que el repositorio fue confirmado como usuario de GH-AW (siempre `True` en este dataset). | |
| *(Otras)* | Variado | Contiene todas las demás columnas del CSV de entrada (como `commits`, `branches`, `mainLanguage`, `license`, `stargazers`, etc.) conservando sus tipos de datos originales. | |

## 2. Tabla: `workflows.parquet`

Esta tabla almacena los archivos Markdown extraídos de la carpeta `.github/workflows/` de cada repositorio, separando su cuerpo (body) de sus metadatos (frontmatter).

| Columna | Tipo de Dato | Significado | Claves |
|---------|--------------|-------------|--------|
| `workflow_id` | String | Identificador único del archivo extraído. Su formato es `{repo_id}/{filename}` (ej. `sparklemotion/nokogiri/report.md`). | **Primary Key** |
| `repo_id` | String | Referencia al repositorio al que pertenece este archivo. | **Foreign Key** (hacia `repositories.repo_id`) |
| `filename` | String | Nombre base del archivo (ej. `report.md`). | |
| `body` | String | El contenido principal en texto plano Markdown del archivo (habiendo retirado el YAML frontmatter). | |

## 3. Tabla: `workflow_attributes.parquet`

Esta tabla almacena, de forma normalizada, toda la información estructurada extraída desde el frontmatter YAML de los archivos Markdown. Gracias a esta estructura en forma de pares Clave-Valor (EAV), el modelo soporta de forma flexible cualquier propiedad YAML sin alterar el esquema.

| Columna | Tipo de Dato | Significado | Claves |
|---------|--------------|-------------|--------|
| `workflow_id` | String | Referencia al archivo Markdown de donde se extrajo este atributo. | **Foreign Key** (hacia `workflows.workflow_id`) |
| `key` | String | El nombre (llave) del metadato extraído del YAML (ej. `name`, `description`, `type`, `version`). | |
| `value` | String | El valor asociado a la llave, casteado a cadena de texto (string) para homogeneizar su almacenamiento en Parquet. | |
