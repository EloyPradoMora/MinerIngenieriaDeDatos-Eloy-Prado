import sys
from miner.cli import app

if __name__ == "__main__":
    # Mantener compatibilidad con el comando original de la Tarea 2
    # Si el usuario ejecuta "python -m miner entrada.csv --output salida.csv"
    # insertamos el subcomando "identify" de manera transparente.
    if len(sys.argv) > 1 and sys.argv[1] not in ["identify", "extract", "--help", "-h"]:
        sys.argv.insert(1, "identify")
        
    app()
