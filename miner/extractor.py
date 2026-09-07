import asyncio
import os
import pandas as pd
import json
from typing import List, Dict, Any
import httpx
import typer
import datetime
import frontmatter

from miner.github import fetch_workflow_files_with_content

def load_extract_progress(progress_file: str) -> set:
    processed = set()
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    processed.add(line.strip())
    return processed

def save_extract_progress(progress_file: str, name: str):
    with open(progress_file, 'a', encoding='utf-8') as f:
        f.write(name + "\n")

def append_jsonl(filename: str, data: dict):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data) + "\n")

async def process_extract_batch(
    repos: List[str],
    token: str,
    progress_file: str,
    out_dir: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore
):
    async def process_single(repo_name: str):
        async with semaphore:
            try:
                owner, name = repo_name.split("/", 1)
            except ValueError:
                save_extract_progress(progress_file, repo_name)
                return

            files = await fetch_workflow_files_with_content(owner, name, token, client)
            if not files:
                save_extract_progress(progress_file, repo_name)
                return
                
            # Identify pairs of .md and .lock.yml
            md_files = {}
            lock_bases = set()
            
            for f in files:
                fname = f["name"]
                if fname.endswith(".md"):
                    md_files[fname[:-3]] = f
                elif fname.endswith(".lock.yml"):
                    lock_bases.add(fname[:-9])
                    
            common_bases = set(md_files.keys()).intersection(lock_bases)
            
            # Extract data
            for base in common_bases:
                f = md_files[base]
                filename = f["name"]
                text = f["text"]
                workflow_id = f"{repo_name}/{filename}"
                
                try:
                    parsed = frontmatter.loads(text)
                    body = parsed.content
                    metadata = parsed.metadata
                except Exception as e:
                    # If parsing fails, store as raw
                    body = text
                    metadata = {}
                    
                # 1. workflows
                append_jsonl(os.path.join(out_dir, "tmp_workflows.jsonl"), {
                    "workflow_id": workflow_id,
                    "repo_id": repo_name,
                    "filename": filename,
                    "body": body
                })
                
                # 2. workflow_attributes
                if isinstance(metadata, dict):
                    for k, v in metadata.items():
                        append_jsonl(os.path.join(out_dir, "tmp_workflow_attributes.jsonl"), {
                            "workflow_id": workflow_id,
                            "key": str(k),
                            "value": str(v)
                        })
            
            save_extract_progress(progress_file, repo_name)

    tasks = [process_single(repo) for repo in repos]
    await asyncio.gather(*tasks)

def generate_parquet(out_dir: str, input_csv: str):
    """Converts the temporary JSONL files and the input CSV to Parquet datasets."""
    typer.echo("Generando tablas Parquet...")
    
    # 1. Repositories
    try:
        df_csv = pd.read_csv(input_csv, low_memory=False)
        # Filter only those that use GH-AW
        if "uses_gh_aw" in df_csv.columns:
            df_csv = df_csv[df_csv["uses_gh_aw"] == True]
        
        # Rename 'name' to 'repo_id' for clarity in the schema
        if "name" in df_csv.columns:
            df_csv.rename(columns={"name": "repo_id"}, inplace=True)
            
        repo_parquet = os.path.join(out_dir, "repositories.parquet")
        df_csv.to_parquet(repo_parquet, index=False)
        typer.echo(f"  - {repo_parquet} creado con {len(df_csv)} filas.")
    except Exception as e:
        typer.secho(f"Error generando repositories.parquet: {e}", fg=typer.colors.RED)

    # 2. Workflows
    wf_jsonl = os.path.join(out_dir, "tmp_workflows.jsonl")
    wf_parquet = os.path.join(out_dir, "workflows.parquet")
    if os.path.exists(wf_jsonl):
        try:
            df_wf = pd.read_json(wf_jsonl, lines=True)
            df_wf.to_parquet(wf_parquet, index=False)
            typer.echo(f"  - {wf_parquet} creado con {len(df_wf)} filas.")
        except ValueError:
            # If empty
            pd.DataFrame(columns=["workflow_id", "repo_id", "filename", "body"]).to_parquet(wf_parquet, index=False)
            typer.echo(f"  - {wf_parquet} creado vacío.")
    
    # 3. Attributes
    attr_jsonl = os.path.join(out_dir, "tmp_workflow_attributes.jsonl")
    attr_parquet = os.path.join(out_dir, "workflow_attributes.parquet")
    if os.path.exists(attr_jsonl):
        try:
            df_attr = pd.read_json(attr_jsonl, lines=True)
            df_attr.to_parquet(attr_parquet, index=False)
            typer.echo(f"  - {attr_parquet} creado con {len(df_attr)} filas.")
        except ValueError:
            pd.DataFrame(columns=["workflow_id", "key", "value"]).to_parquet(attr_parquet, index=False)
            typer.echo(f"  - {attr_parquet} creado vacío.")

async def run_extract_async(input_csv: str, out_dir: str, token: str):
    os.makedirs(out_dir, exist_ok=True)
    progress_file = os.path.join(out_dir, "extract_progress.txt")
    
    typer.echo("Leyendo archivo CSV de repositorios GH-AW...")
    try:
        df = pd.read_csv(input_csv, usecols=["name", "uses_gh_aw"])
    except ValueError:
        typer.secho("Error: El CSV debe contener las columnas 'name' y 'uses_gh_aw'.", fg=typer.colors.RED)
        raise typer.Exit(1)
        
    df_ghaw = df[df["uses_gh_aw"] == True]
    all_repos = df_ghaw["name"].dropna().unique().tolist()
    
    while True:
        processed = load_extract_progress(progress_file)
        typer.echo(f"Se han extraído datos de {len(processed)} repositorios hasta ahora.")
        
        repos_to_process = [repo for repo in all_repos if repo not in processed]
        
        if not repos_to_process:
            break
            
        typer.echo(f"Repositorios pendientes por extraer: {len(repos_to_process)}")
        
        semaphore = asyncio.Semaphore(20)
        chunk_size = 1000
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=20)
        
        try:
            async with httpx.AsyncClient(limits=limits, timeout=20.0) as client:
                for i in range(0, len(repos_to_process), chunk_size):
                    chunk = repos_to_process[i:i + chunk_size]
                    typer.echo(f"Extrayendo bloque {i//chunk_size + 1}/{(len(repos_to_process)-1)//chunk_size + 1} ({len(chunk)} repos)...")
                    await process_extract_batch(chunk, token, progress_file, out_dir, client, semaphore)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (403, 429):
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                typer.secho(f"\n[{now}] Límite de la API de GitHub alcanzado (Status {e.response.status_code}).", fg=typer.colors.RED)
                typer.secho("Durmiendo por 61 minutos para recuperar la cuota. No cierres esta ventana...", fg=typer.colors.YELLOW)
                await asyncio.sleep(61 * 60)
                now_wake = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                typer.secho(f"\n[{now_wake}] Despertando y reanudando la extracción...", fg=typer.colors.GREEN)
                continue
            else:
                raise
                
    typer.echo("Extracción de GitHub completada.")
    generate_parquet(out_dir, input_csv)
