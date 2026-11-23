"""Conexión a SQLite y creación de las tablas a partir de db/schema.sql."""
import sqlite3
from contextlib import contextmanager

from . import config
from .security import hash_password


def conectar() -> sqlite3.Connection:
    con = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


@contextmanager
def conexion():
    con = conectar()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def get_db():
    """Dependencia de FastAPI: una conexión por solicitud."""
    with conexion() as con:
        yield con


def init_db() -> None:
    """Crea las tablas si no existen y registra los usuarios iniciales."""
    with conexion() as con:
        con.executescript(config.SCHEMA_PATH.read_text(encoding="utf-8"))
        hay_usuarios = con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        if not hay_usuarios:
            con.executemany(
                "INSERT INTO usuarios (usuario, nombre, password_hash, rol) VALUES (?, ?, ?, ?)",
                [
                    (config.ADMIN_USUARIO, "Administrador", hash_password(config.ADMIN_PASSWORD), "admin"),
                    (config.DOCENTE_USUARIO, "Docente", hash_password(config.DOCENTE_PASSWORD), "docente"),
                ],
            )
