"""Crea la base de datos desde db/schema.sql, registra los usuarios iniciales y entrena el modelo v1.

Uso (desde la carpeta backend):  python scripts/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.database import init_db  # noqa: E402
from app.ml.servicio import asegurar_modelo_inicial  # noqa: E402

if __name__ == "__main__":
    init_db()
    print(f"Base de datos lista en {config.DATABASE_PATH}")
    asegurar_modelo_inicial()
    print("Modelo inicial entrenado y registrado")
