import frontmatter
import os
import pytest
import pandas as pd

def test_frontmatter_parsing():
    content = """---
name: "Daily Report"
type: summary
version: 1.2
---

# This is the body
Some markdown text here.
"""
    parsed = frontmatter.loads(content)
    
    assert parsed.metadata["name"] == "Daily Report"
    assert parsed.metadata["type"] == "summary"
    assert parsed.metadata["version"] == 1.2
    assert "This is the body" in parsed.content

def test_generate_parquet(tmp_path):
    # Simular CSV
    df = pd.DataFrame({
        "name": ["owner/repo1", "owner/repo2"],
        "uses_gh_aw": [True, False],
        "stars": [10, 20]
    })
    csv_path = str(tmp_path / "test_input.csv")
    df.to_csv(csv_path, index=False)
    
    # Importar aquí para evitar que se ejecute al importar
    from miner.extractor import generate_parquet
    
    # Crear un JSONL falso
    import json
    wf_jsonl = str(tmp_path / "tmp_workflows.jsonl")
    with open(wf_jsonl, "w") as f:
        f.write(json.dumps({"workflow_id": "owner/repo1/file.md", "repo_id": "owner/repo1", "filename": "file.md", "body": "test"}) + "\n")
        
    generate_parquet(str(tmp_path), csv_path)
    
    # Verificar parquets
    repos_df = pd.read_parquet(str(tmp_path / "repositories.parquet"))
    assert len(repos_df) == 1 # solo el True
    assert "repo_id" in repos_df.columns
    
    wf_df = pd.read_parquet(str(tmp_path / "workflows.parquet"))
    assert len(wf_df) == 1
    assert wf_df.iloc[0]["workflow_id"] == "owner/repo1/file.md"
