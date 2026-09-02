# Miner

Miner es una aplicación de línea de comandos (CLI) hecho en Python que identifica repositorios de GitHub que utilizan **GitHub Agentic Workflows (GH-AW)**.

## ¿Qué problema resuelve Miner?

A partir de un archivo CSV con una lista extensa de repositorios (obtenida previamente), Miner consulta la API GraphQL de GitHub para inspeccionar el directorio `.github/workflows/` de cada repositorio. Identifica automáticamente si un repositorio utiliza GH-AW buscando la presencia de archivos `.md` que posean su correspondiente archivo compilado `.lock.yml` (por ejemplo, `report.md` y `report.lock.yml`). Finalmente, Miner genera un nuevo archivo CSV idéntico al de entrada, añadiendo una nueva columna `uses_gh_aw` (`True` o `False`) para indicar si el repositorio hace uso de estas herramientas.

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

Miner se ejecuta a través de Python, apuntando al paquete `miner`.

### Sintaxis
```bash
python -m miner ruta/al/archivo/entrada.csv --output ruta/al/archivo/salida.csv
```

### Ejemplo de uso
```bash
python -m miner "results.csv" --output repositorios_ghaw.csv
```

### ¿Qué archivo recibe como entrada?
Recibe un archivo CSV que debe contener, como mínimo, una columna llamada `name` con el identificador del repositorio en el formato `propietario/repositorio` (por ejemplo, `sparklemotion/nokogiri`). Todas las demás columnas del CSV se mantendrán intactas en el archivo de salida.

### ¿Qué archivo genera como salida?
Genera un archivo CSV (`repositorios_ghaw.csv` en el ejemplo) que contiene exactamente **todos los repositorios y columnas del archivo de entrada**, pero con **una columna adicional al final llamada `uses_gh_aw`** que contendrá `True` si el repositorio utiliza GH-AW, o `False` en caso contrario.

### Tolerancia a fallos y reanudación
Junto a su archivo de entrada, Miner creará automáticamente un archivo de progreso temporal (por ejemplo, `results.csv.progress.jsonl`). Si se corta la luz o se detiene el proceso con `Ctrl+C`, **no se perdera nada**. Para reanudar simplemente vuelva a ejecutar el mismo comando empleado originalmente y Miner reanudará desde el último repositorio procesado. Una vez finalice con todos los repositorios, generará el archivo CSV de salida final.

---

## Ejecutar Pruebas

Miner incluye pruebas automatizadas creadas con `pytest` para verificar la lógica de identificación de GH-AW. Para ejecutarlas:

```bash
pytest tests/
```