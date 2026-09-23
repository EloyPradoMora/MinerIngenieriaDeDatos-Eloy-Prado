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
            lock_files = {}
            lock_bases = set()
            
            for f in files:
                fname = f["name"]
                if fname.endswith(".md"):
                    md_files[fname[:-3]] = f
                elif fname.endswith(".lock.yml"):
                    lock_files[fname[:-9]] = f
                    lock_bases.add(fname[:-9])
                    
            common_bases = set(md_files.keys()).intersection(lock_bases)
            
            import yaml
            
            # Extract data
            for base in common_bases:
                f_md = md_files[base]
                f_lock = lock_files[base]
                
                filename = f_md["name"]
                text_md = f_md["text"]
                lock_text = f_lock["text"]
                
                markdown_id = f"{repo_name}/{filename}"
                lock_id = f"{repo_name}/{base}.lock.yml"
                
                try:
                    parsed = frontmatter.loads(text_md)
                    body = parsed.content
                    metadata = parsed.metadata
                    formater = yaml.dump(metadata, allow_unicode=True, default_flow_style=False) if metadata else ""
                except Exception as e:
                    # If parsing fails, store as raw
                    body = text_md
                    formater = ""
                    
                # 1. markdown
                append_jsonl(os.path.join(out_dir, "tmp_markdown.jsonl"), {
                    "markdown_id": markdown_id,
                    "repo_id": repo_name,
                    "filename": filename,
                    "formater": formater,
                    "body": body
                })
                
                # 2. lock
                append_jsonl(os.path.join(out_dir, "tmp_lock.jsonl"), {
                    "lock_id": lock_id,
                    "markdown_id": markdown_id,
                    "yaml_content": lock_text
                })
            
            save_extract_progress(progress_file, repo_name)

    tasks = [process_single(repo) for repo in repos]
    await asyncio.gather(*tasks)

def generate_parquet(out_dir: str, input_csv: str):
    """Converts the temporary JSONL files and the input CSV to Parquet datasets."""
    typer.echo("Generando tablas Parquet...")
    
    # 1. Repository
    try:
        df_csv = pd.read_csv(input_csv, low_memory=False)
        # Filter only those that use GH-AW
        if "uses_gh_aw" in df_csv.columns:
            df_csv = df_csv[df_csv["uses_gh_aw"] == True]
        
        # Rename 'name' to 'repo_id' for clarity in the schema
        if "name" in df_csv.columns:
            df_csv.rename(columns={"name": "repo_id"}, inplace=True)
            
        repo_parquet = os.path.join(out_dir, "repository.parquet")
        df_csv.to_parquet(repo_parquet, index=False)
        typer.echo(f"  - {repo_parquet} creado con {len(df_csv)} filas.")
    except Exception as e:
        typer.secho(f"Error generando repository.parquet: {e}", fg=typer.colors.RED)

    # 2. MarkDown
    md_jsonl = os.path.join(out_dir, "tmp_markdown.jsonl")
    md_parquet = os.path.join(out_dir, "markdown.parquet")
    if os.path.exists(md_jsonl):
        try:
            df_md = pd.read_json(md_jsonl, lines=True)
            df_md.to_parquet(md_parquet, index=False)
            typer.echo(f"  - {md_parquet} creado con {len(df_md)} filas.")
        except ValueError:
            # If empty
            pd.DataFrame(columns=["markdown_id", "repo_id", "filename", "formater", "body"]).to_parquet(md_parquet, index=False)
            typer.echo(f"  - {md_parquet} creado vacío.")
    else:
        pd.DataFrame(columns=["markdown_id", "repo_id", "filename", "formater", "body"]).to_parquet(md_parquet, index=False)
    
    # 3. Lock
    lock_jsonl = os.path.join(out_dir, "tmp_lock.jsonl")
    lock_parquet = os.path.join(out_dir, "lock.parquet")
    if os.path.exists(lock_jsonl):
        try:
            df_lock = pd.read_json(lock_jsonl, lines=True)
            df_lock.to_parquet(lock_parquet, index=False)
            typer.echo(f"  - {lock_parquet} creado con {len(df_lock)} filas.")
        except ValueError:
            pd.DataFrame(columns=["lock_id", "markdown_id", "yaml_content"]).to_parquet(lock_parquet, index=False)
            typer.echo(f"  - {lock_parquet} creado vacío.")
    else:
        pd.DataFrame(columns=["lock_id", "markdown_id", "yaml_content"]).to_parquet(lock_parquet, index=False)

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
