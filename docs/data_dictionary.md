# Diccionario de Datos

Este documento describe la estructura de los archivos `.parquet` generados por el proceso de extracción de GitHub Agentic Workflows.

## 1. Tabla: `repository.parquet`

Esta tabla almacena la información original de los repositorios procesados y filtrados. Solo contiene repositorios que hacen uso de GH-AW (`uses_gh_aw == True`).

| Columna | Tipo de Dato | Significado | Claves |
|---------|--------------|-------------|--------|
| `repo_id` | String | Identificador único del repositorio en la plataforma (formato: `owner/repo`). Corresponde a la columna `name` del CSV original. | **Primary Key** |
| `uses_gh_aw` | Boolean | Indica que el repositorio fue confirmado como usuario de GH-AW (siempre `True` en este dataset). | |
| *(Otras)* | Variado | Contiene todas las demás columnas del CSV de entrada (como `commits`, `branches`, `mainLanguage`, `license`, `stargazers`, etc.) conservando sus tipos de datos originales. | |

## 2. Tabla: `markdown.parquet`

Esta tabla almacena los archivos Markdown extraídos de la carpeta `.github/workflows/` de cada repositorio, junto a su frontmatter asociado.

| Columna | Tipo de Dato | Significado | Claves |
|---------|--------------|-------------|--------|
| `markdown_id` | String | Identificador único del archivo extraído. Su formato es `{repo_id}/{filename}` (ej. `sparklemotion/nokogiri/report.md`). | **Primary Key** |
| `repo_id` | String | Referencia al repositorio al que pertenece este archivo. | **Foreign Key** (hacia `repository.repo_id`) |
| `filename` | String | Nombre base del archivo (ej. `report.md`). | |
| `formater` | String | El bloque de metadatos (Frontmatter YAML) en formato de texto crudo. | |
| `body` | String | El contenido principal en texto plano Markdown del archivo (habiendo retirado el YAML frontmatter). | |

## 3. Tabla: `lock.parquet`

Esta tabla almacena el contenido del archivo `.lock.yml` correspondiente al archivo Markdown, garantizando una relación 1:1.

| Columna | Tipo de Dato | Significado | Claves |
|---------|--------------|-------------|--------|
| `lock_id` | String | Identificador único del archivo lock. Su formato es `{repo_id}/{filename.lock.yml}`. | **Primary Key** |
| `markdown_id` | String | Referencia al archivo Markdown con el mismo nombre base. | **Foreign Key** (hacia `markdown.markdown_id`), Relación 1:1 |
| `yaml_content`| String | Contenido en texto crudo (sin procesar) del archivo `.lock.yml`. | |

