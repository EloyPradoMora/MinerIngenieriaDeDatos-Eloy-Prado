# Diagrama Entidad-Relación (GH-AW)

Este diagrama representa el modelo relacional generado a partir de la extracción de archivos Markdown y Lock de GitHub Agentic Workflows.

```mermaid
erDiagram
    REPOSITORY ||--o{ MARKDOWN : "contiene"
    MARKDOWN ||--|| LOCK : "tiene"

    REPOSITORY {
        string repo_id PK "owner/repo (e.g. sparklemotion/nokogiri)"
        boolean uses_gh_aw "Indicador de si utiliza GH-AW"
        int commits
        int branches
        string mainLanguage
        string license
    }

    MARKDOWN {
        string markdown_id PK "owner/repo/filename.md"
        string repo_id FK "Referencia al repositorio"
        string filename "Nombre del archivo (ej. daily-report.md)"
        string formater "Metadatos Frontmatter (YAML)"
        string body "Cuerpo del archivo Markdown"
    }

    LOCK {
        string lock_id PK "owner/repo/filename.lock.yml"
        string markdown_id FK "Referencia al archivo Markdown"
        string yaml_content "Contenido crudo del archivo .lock.yml"
    }
```
