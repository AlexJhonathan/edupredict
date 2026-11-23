"""Configuración de la API. Los valores se leen del archivo .env (ver .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _ruta(nombre: str, defecto: str) -> Path:
    valor = Path(os.getenv(nombre, defecto))
    return valor if valor.is_absolute() else BASE_DIR / valor


STORAGE_DIR = _ruta("STORAGE_DIR", "storage")
DATABASE_PATH = _ruta("DATABASE_PATH", str(STORAGE_DIR / "edupredict.db"))
MODELOS_DIR = STORAGE_DIR / "modelos"
DATASETS_DIR = STORAGE_DIR / "datasets"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"
DATASET_INICIAL = _ruta("DATASET_INICIAL", "data/StudentPerformanceFactors.csv")

JWT_SECRET = os.getenv("JWT_SECRET", "cambia-esta-clave-en-produccion-por-una-larga")
JWT_ALGORITMO = "HS256"
JWT_MINUTOS = int(os.getenv("JWT_MINUTOS", "480"))

CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

ADMIN_USUARIO = os.getenv("ADMIN_USUARIO", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DOCENTE_USUARIO = os.getenv("DOCENTE_USUARIO", "docente")
DOCENTE_PASSWORD = os.getenv("DOCENTE_PASSWORD", "docente123")

MAX_UPLOAD_MB = float(os.getenv("MAX_UPLOAD_MB", "10"))
SEED = 42

for carpeta in (STORAGE_DIR, MODELOS_DIR, DATASETS_DIR):
    carpeta.mkdir(parents=True, exist_ok=True)
