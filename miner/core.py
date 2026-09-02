from typing import List

def uses_github_agentic_workflows(filenames: List[str]) -> bool:
    """
    Checks if a list of filenames from .github/workflows/ contains
    at least one pair of <name>.md and <name>.lock.yml.
    """
    if not filenames:
        return False
        
    md_files = set()
    lock_files = set()
    
    for filename in filenames:
        if filename.endswith(".md"):
            md_files.add(filename[:-3]) # get base name without .md
        elif filename.endswith(".lock.yml"):
            lock_files.add(filename[:-9]) # get base name without .lock.yml
            
    # Find intersection of base names
    common_bases = md_files.intersection(lock_files)
    
    return len(common_bases) > 0
