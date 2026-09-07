# Miner

Miner es una aplicación de línea de comandos (CLI) hecho en Python que identifica repositorios de GitHub que utilizan **GitHub Agentic Workflows (GH-AW)**.

## ¿Qué problema resuelve Miner?

A partir de un archivo CSV con una lista extensa de repositorios (obtenida previamente), Miner consulta la API GraphQL de GitHub para inspeccionar el directorio `.github/workflows/` de cada repositorio. Identifica automáticamente si un repositorio utiliza GH-AW y genera un nuevo archivo CSV idéntico al de entrada, añadiendo una nueva columna `uses_gh_aw`.

En su **versión extendida (Tarea 3)**, Miner también es capaz de extraer el contenido de los archivos Markdown de esos repositorios identificados. Separa el *frontmatter* YAML del cuerpo del texto, normaliza los datos y los guarda localmente como un dataset relacional en formato **Apache Parquet**.

Miner es **robusto a interrupciones**: guarda su progreso continuamente. Si la ejecución se interrumpe (por apagado del equipo, pérdida de conexión o cierre de terminal), se puede volver a ejecutar el comando y este retomará exactamente donde se quedó, sin perder los avances ni realizar consultas duplicadas a GitHub. Además, utiliza la **API GraphQL de GitHub** con peticiones **asíncronas concurrentes** para extraer los datos de forma extremadamente rápida.

---

## Requisitos previos

- Python 3.9 o superior.
- Una cuenta de GitHub.
- Un Token de Acceso Personal (PAT) de GitHub.

---

## 1. Preparar el entorno Python e instalar dependencias

Debe clonar o descargar este repositorio y abrir un terminal en la carpeta principal.

Debe crear un entorno virtual:
```bash
python -m venv .venv
```

Activar el entorno virtual:
- En **Windows**:
  ```bash
  .venv\Scripts\activate
  ```
- En **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

Instalar las dependencias:
```bash
pip install -r requirements.txt
```

---

## 2. Configurar el Token de GitHub

Miner requiere un token de GitHub para consultar la API. 

1. Para conseguirlo, dirijase a [GitHub Tokens (Classic)](https://github.com/settings/tokens) o cree un Fine-grained token. (No requiere permisos especiales si los repositorios son públicos, pero un token base es necesario para los límites de tasa de la API).
2. Crea un archivo llamado `.env` en el directorio raíz del proyecto.
3. Agregue su token al archivo de la siguiente manera:
   ```env
   GITHUB_TOKEN=tu_token_aqui_ghp_xxxxxxxxxx
   ```

---

## 3. Ejecutar Miner

Miner cuenta con comandos diferentes para cada tarea, manteniendo sus funcionalidades separadas.

### Comando 1: Identificación (Tarea 2)
Sirve para identificar los repositorios GH-AW y generar el nuevo CSV.

```bash
python -m miner identify "results (1).csv" --output repositorios_ghaw.csv
```
*(Nota: Por compatibilidad, el comando original sin la palabra "identify" también funciona exactamente igual).*

### Comando 2: Extracción y Generación de Dataset Parquet (Tarea 3)
A partir del archivo CSV generado en el paso anterior, este comando descargará el texto de los archivos `.md`, procesará su *frontmatter* YAML y exportará las tablas en formato Parquet a la carpeta indicada.

```bash
python -m miner extract repositorios_ghaw.csv --output-dir dataset_parquet/
```
Al finalizar, encontrarás tres archivos `.parquet` en esa carpeta: `repositories.parquet`, `workflows.parquet`, y `workflow_attributes.parquet`.

### ¿Qué archivo recibe como entrada?
Recibe un archivo CSV que debe contener, como mínimo, una columna llamada `name` con el identificador del repositorio en el formato `propietario/repositorio` (por ejemplo, `sparklemotion/nokogiri`). Todas las demás columnas del CSV se mantendrán intactas en el archivo de salida.

### ¿Qué archivo genera como salida?
Genera un archivo CSV (`repositorios_ghaw.csv` en el ejemplo) que contiene exactamente **todos los repositorios y columnas del archivo de entrada**, pero con **una columna adicional al final llamada `uses_gh_aw`** que contendrá `True` si el repositorio utiliza GH-AW, o `False` en caso contrario.

### Tolerancia a fallos y reanudación
Miner creará automáticamente archivos de progreso temporal (`.progress.jsonl` o `extract_progress.txt`). Si se corta la luz, o si te bloquea la API de GitHub por el límite de peticiones (Rate Limit), **no perderás nada**. Simplemente vuelve a ejecutar el mismo comando y Miner reanudará desde el último repositorio procesado.

---

## 4. Documentación del Dataset

En el directorio `docs/` de este proyecto encontrarás:
- **ER_diagram.md**: El diagrama Entidad-Relación del dataset generado.
- **data_dictionary.md**: El diccionario de datos explicando qué contiene cada archivo `.parquet` y sus tipos de datos.

---

## 5. Publicar en Hugging Face Datasets

Para subir el dataset generado a Hugging Face, Miner incluye un script auxiliar:

1. Crea un Access Token (con permisos de **Write**) en [Hugging Face Settings](https://huggingface.co/settings/tokens).
2. Guárdalo en tu archivo `.env` añadiendo la línea:
   ```env
   HF_TOKEN=hf_tu_token_aqui
   ```
3. Ejecuta el script de subida pasando el nombre del directorio donde se guardaron los `.parquet` y el nombre de tu nuevo repositorio en Hugging Face:
   ```bash
   python upload_to_hf.py dataset_parquet/ "tu_usuario_hf/miner_ghaw_dataset"
   ```
El script creará automáticamente el repositorio, redactará un `README.md` básico y subirá los 3 archivos Parquet.

---

## Ejecutar Pruebas

Miner incluye pruebas automatizadas creadas con `pytest` para verificar la lógica de identificación de GH-AW. Para ejecutarlas:

```bash
pytest tests/
```