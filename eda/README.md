# Análisis Exploratorio de Datos (EDA) - GitHub Agentic Workflows

Este directorio contiene el análisis exploratorio (EDA) de los repositorios que utilizan GitHub Agentic Workflows. El análisis se ha dividido en dos Jupyter Notebooks.

## 1. Origen de los Datos
El dataset base analizado en estos notebooks está publicado y disponible públicamente en Hugging Face en el siguiente enlace:
👉 [EloyPradoMora/BitacoraDeGH-AW](https://huggingface.co/datasets/EloyPradoMora/BitacoraDeGH-AW)

> **Nota:** No necesitas descargar los archivos Parquet manualmente; el *Notebook 1* está configurado para leerlos directamente desde Hugging Face mediante Pandas.

## 2. Configuración del Entorno y Dependencias

Para reproducir este análisis, debes tener instalado el entorno virtual del proyecto con las siguientes bibliotecas de manipulación de datos, graficado y jupyter:

```bash
# Si usas venv (Pip):
python -m pip install jupyterlab ipykernel pandas pyarrow matplotlib seaborn fsspec

# Si usas uv:
uv add jupyterlab ipykernel pandas pyarrow matplotlib seaborn fsspec
```

## 3. Ejecución de los Notebooks

Para iniciar el entorno de JupyterLab, ejecuta el siguiente comando en la raíz de tu proyecto:
```bash
jupyter lab
```

Una vez en el entorno interactivo de JupyterLab, asegúrate de seleccionar el *kernel* correspondiente a tu entorno virtual (`Python 3 (ipykernel)` o similar).

### Orden de Ejecución

Debes ejecutar los notebooks **estrictamente en este orden** de principio a fin, ya que el primero prepara los datos que usa el segundo:

1. **`01_descripcion_y_calidad.ipynb`**: Descarga los datos de Hugging Face, revisa la calidad (nulos, duplicados, integridad), y guarda las tablas limpias localmente en la carpeta `eda/data/processed/`.
2. **`02_exploracion_y_hallazgos.ipynb`**: Carga las tablas limpias y realiza análisis estadísticos, distribuciones y generación de gráficos respondiendo preguntas exploratorias.
