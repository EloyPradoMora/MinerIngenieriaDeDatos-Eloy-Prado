import typer
import os
from huggingface_hub import HfApi
import pandas as pd

app = typer.Typer(help="Sube el dataset a Hugging Face.")

@app.command()
def main(
    dataset_dir: str = typer.Argument(..., help="dataset_parquet)"),
    repo_id: str = typer.Argument(..., help="EloyPradoMora/BitacoraDeGH-AW"),
):
    """
    Sube los archivos Parquet generados a un repositorio de Hugging Face Datasets.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.environ.get("HF_TOKEN")
    if not token:
        typer.secho("Error: La variable de entorno HF_TOKEN no está configurada.", fg=typer.colors.RED)
        typer.echo("Crea un Access Token en https://huggingface.co/settings/tokens con permisos de escritura.")
        typer.echo("Agrégalo a tu archivo .env o impórtalo en tu consola.")
        raise typer.Exit(1)

    api = HfApi()

    typer.echo(f"Verificando/Creando repositorio {repo_id}...")
    try:
        api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True, token=token)
    except Exception as e:
        typer.secho(f"Error creando/verificando el repositorio: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    archivos = ["repositories.parquet", "workflows.parquet", "workflow_attributes.parquet"]
    
    for archivo in archivos:
        ruta = os.path.join(dataset_dir, archivo)
        if os.path.exists(ruta):
            typer.echo(f"Subiendo {archivo}...")
            api.upload_file(
                path_or_fileobj=ruta,
                path_in_repo=archivo,
                repo_id=repo_id,
                repo_type="dataset",
                token=token
            )
            typer.secho(f"¡{archivo} subido exitosamente!", fg=typer.colors.GREEN)
        else:
            typer.secho(f"Advertencia: No se encontró el archivo {ruta}", fg=typer.colors.YELLOW)

    # Subir un pequeño README.md si no existe localmente
    readme_content = f"""
---
license: mit
task_categories:
- text-classification
language:
- en
---

# GitHub Agentic Workflows Dataset

Este dataset contiene información sobre repositorios que utilizan GitHub Agentic Workflows, junto con el contenido extraído de sus archivos Markdown y los metadatos de su frontmatter YAML.

- **repositories.parquet**: Lista de repositorios verificados.
- **workflows.parquet**: Archivos markdown con su contenido.
- **workflow_attributes.parquet**: Atributos clave-valor extraídos del YAML frontmatter.
"""
    readme_path = os.path.join(dataset_dir, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
    typer.echo("Subiendo README.md...")
    api.upload_file(
        path_or_fileobj=readme_path,
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
        token=token
    )

    typer.secho(f"\n¡Dataset publicado con éxito en https://huggingface.co/datasets/{repo_id}!", fg=typer.colors.CYAN)

if __name__ == "__main__":
    app()
