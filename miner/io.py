import pandas as pd
import json
import os
from typing import Dict, Set

def load_progress(progress_file: str) -> Dict[str, bool]:
    """Loads processed repositories from a JSONL file."""
    processed = {}
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        processed[data["name"]] = data["uses_gh_aw"]
                    except json.JSONDecodeError:
                        pass
    return processed

def save_progress(progress_file: str, name: str, uses_gh_aw: bool):
    """Appends a single repository's result to the progress file."""
    with open(progress_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"name": name, "uses_gh_aw": uses_gh_aw}) + "\n")

def generate_final_csv(input_csv: str, output_csv: str, progress_file: str):
    """
    Reads the input CSV in chunks, merges with progress data,
    and writes to the output CSV.
    """
    processed = load_progress(progress_file)
    
    # Write the header first
    first_chunk = True
    
    # Process in chunks to handle very large CSV files (e.g. 600MB+)
    for chunk in pd.read_csv(input_csv, chunksize=10000, low_memory=False):
        # Create the new column by mapping the 'name' column
        # If for some reason a repo wasn't processed, default to False
        chunk["uses_gh_aw"] = chunk["name"].map(lambda x: processed.get(x, False))
        
        # Write to output file
        mode = 'w' if first_chunk else 'a'
        header = first_chunk
        chunk.to_csv(output_csv, mode=mode, header=header, index=False)
        first_chunk = False
