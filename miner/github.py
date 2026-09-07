import httpx
from typing import List

GRAPHQL_URL = "https://api.github.com/graphql"

async def fetch_workflow_files(owner: str, name: str, token: str, client: httpx.AsyncClient) -> List[str]:
    """
    Fetches the list of filenames in the .github/workflows directory of a GitHub repository
    using the GraphQL API.
    """
    query = """
    query ($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        object(expression: "HEAD:.github/workflows") {
          ... on Tree {
            entries {
              name
            }
          }
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    variables = {
        "owner": owner,
        "name": name
    }
    
    try:
        response = await client.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10.0
        )
        
        # Simple rate limit handling: if 403 or 429, we should raise to let the caller handle it.
        if response.status_code in (403, 429):
            response.raise_for_status()
            
        # Don't raise for 404 (repo not found), just return empty.
        if response.status_code == 404:
            return []
            
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            # Often happens if repo is empty, doesn't exist, etc.
            return []
            
        repo_data = data.get("data", {}).get("repository")
        if not repo_data:
            return []
            
        tree_object = repo_data.get("object")
        if not tree_object:
            # .github/workflows directory doesn't exist
            return []
            
        entries = tree_object.get("entries", [])
        return [entry["name"] for entry in entries]
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (403, 429):
            # Re-raise rate limit errors so caller can sleep
            raise
        return []
    except httpx.RequestError as e:
        # Network errors etc
        print(f"Network error querying {owner}/{name}: {e}")
        return []
    except Exception as e:
        if "client has been closed" not in str(e):
            print(f"Error querying {owner}/{name}: {e}")
        return []

async def fetch_workflow_files_with_content(owner: str, name: str, token: str, client: httpx.AsyncClient) -> List[dict]:
    """
    Fetches the list of filenames AND their text content in the .github/workflows directory
    using the GraphQL API.
    Returns a list of dicts: [{'name': '...', 'text': '...'}]
    """
    query = """
    query ($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        object(expression: "HEAD:.github/workflows") {
          ... on Tree {
            entries {
              name
              object {
                ... on Blob {
                  text
                }
              }
            }
          }
        }
      }
    }
    """
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    variables = {
        "owner": owner,
        "name": name
    }
    
    try:
        response = await client.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=15.0
        )
        
        if response.status_code in (403, 429):
            response.raise_for_status()
            
        if response.status_code == 404:
            return []
            
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            return []
            
        repo_data = data.get("data", {}).get("repository")
        if not repo_data:
            return []
            
        tree_object = repo_data.get("object")
        if not tree_object:
            return []
            
        entries = tree_object.get("entries", [])
        
        result = []
        for entry in entries:
            file_name = entry.get("name")
            obj = entry.get("object") or {}
            text = obj.get("text")
            if text is not None:
                result.append({"name": file_name, "text": text})
            else:
                # Might be a subdirectory, we only want files
                result.append({"name": file_name, "text": ""})
                
        return result
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (403, 429):
            raise
        return []
    except httpx.RequestError as e:
        return []
    except Exception as e:
        if "client has been closed" not in str(e):
            pass
        return []
