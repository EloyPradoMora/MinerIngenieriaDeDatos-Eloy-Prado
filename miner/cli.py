import typer
import asyncio
import os
import pandas as pd
from typing import List
from dotenv import load_dotenv
import httpx
import datetime
import asyncio
import os
import pandas as pd
from typing import List
from dotenv import load_dotenv
import httpx

from miner.io import load_progress, save_progress, generate_final_csv
from miner.github import fetch_workflow_files
from miner.core import uses_github_agentic_workflows
from miner.extractor import run_extract_async

app = typer.Typer(help="Miner: Identifies GitHub repositories using GitHub Agentic Workflows.")

async def process_batch(
    repos: List[str],
    token: str,
    progress_file: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore
):
    async def process_single(repo_name: str):
        async with semaphore:
            try:
                owner, name = repo_name.split("/", 1)
            except ValueError:
                # Invalid name format
                save_progress(progress_file, repo_name, False)
                return

            files = await fetch_workflow_files(owner, name, token, client)
            is_gh_aw = uses_github_agentic_workflows(files)
            save_progress(progress_file, repo_name, is_gh_aw)

    tasks = [process_single(repo) for repo in repos]
    await asyncio.gather(*tasks)

async def run_miner_async(input_csv: str, output_csv: str, progress_file: str, token: str):
    typer.echo("Leyendo archivo CSV de entrada...")
    try:
        df = pd.read_csv(input_csv, usecols=["name"])
    except ValueError:
        typer.secho("Error: El archivo CSV debe contener una columna 'name'.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    all_repos = df["name"].dropna().unique().tolist()
    
    while True:
        processed = load_progress(progress_file)
        typer.echo(f"Se han procesado {len(processed)} repositorios hasta ahora.")
        
        repos_to_process = [repo for repo in all_repos if repo not in processed]
        
        if not repos_to_process:
            break
            
        typer.echo(f"Repositorios pendientes por procesar: {len(repos_to_process)}")
        
        semaphore = asyncio.Semaphore(20)
        chunk_size = 1000
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=20)
        
        try:
            async with httpx.AsyncClient(limits=limits, timeout=15.0) as client:
                for i in range(0, len(repos_to_process), chunk_size):
                    chunk = repos_to_process[i:i + chunk_size]
                    typer.echo(f"Procesando bloque {i//chunk_size + 1}/{(len(repos_to_process)-1)//chunk_size + 1} ({len(chunk)} repos)...")
                    await process_batch(chunk, token, progress_file, client, semaphore)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (403, 429):
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                typer.secho(f"\n[{now}] Límite de la API de GitHub alcanzado (Status {e.response.status_code}).", fg=typer.colors.RED)
                typer.secho("Durmiendo por 61 minutos para recuperar la cuota. No cierres esta ventana...", fg=typer.colors.YELLOW)
                
                # Dormir 61 minutos (61 * 60 segundos)
                await asyncio.sleep(61 * 60)
                
                now_wake = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                typer.secho(f"\n[{now_wake}] Despertando y reanudando el proceso...", fg=typer.colors.GREEN)
                continue
            else:
                raise
                
    typer.echo("Todos los repositorios procesados. Generando CSV final...")
    generate_final_csv(input_csv, output_csv, progress_file)
    typer.echo(f"¡Listo! Archivo generado en {output_csv}")

@app.command(name="identify")
def identify(
    input_csv: str = typer.Argument(..., help="Path to the input CSV file containing repositories"),
    output: str = typer.Option(..., "--output", "-o", help="Path to the output CSV file")
):
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        typer.secho("Error: GITHUB_TOKEN environment variable not set. Please set it in .env file.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    if not os.path.exists(input_csv):
        typer.secho(f"Error: Input file {input_csv} does not exist.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    # We use a sidecar progress file next to the input file
    progress_file = f"{input_csv}.progress.jsonl"
    
    try:
        asyncio.run(run_miner_async(input_csv, output, progress_file, token))
    except KeyboardInterrupt:
        typer.secho("\nProceso interrumpido por el usuario. El progreso ha sido guardado. Vuelve a ejecutar para reanudar.", fg=typer.colors.YELLOW)

@app.command(name="extract")
def extract(
    input_csv: str = typer.Argument(..., help="Path to the input CSV file containing GH-AW repositories"),
    output_dir: str = typer.Option(..., "--output-dir", "-d", help="Directory to save the generated Parquet files")
):
    """
    Extrae el contenido de los archivos GH-AW y genera un dataset en formato Parquet.
    """
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        typer.secho("Error: GITHUB_TOKEN environment variable not set. Please set it in .env file.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    if not os.path.exists(input_csv):
        typer.secho(f"Error: Input file {input_csv} does not exist.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    try:
        asyncio.run(run_extract_async(input_csv, output_dir, token))
    except KeyboardInterrupt:
        typer.secho("\nProceso interrumpido por el usuario. El progreso ha sido guardado. Vuelve a ejecutar para reanudar.", fg=typer.colors.YELLOW)

if __name__ == "__main__":
    app()
