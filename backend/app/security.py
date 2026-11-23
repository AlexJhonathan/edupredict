"""Contraseñas con bcrypt y autenticación con JWT."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from . import config

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def crear_token(usuario: dict) -> str:
    ahora = datetime.now(timezone.utc)
    datos = {"sub": str(usuario["id"]), "usuario": usuario["usuario"], "rol": usuario["rol"],
             "iat": ahora, "exp": ahora + timedelta(minutes=config.JWT_MINUTOS)}
    return jwt.encode(datos, config.JWT_SECRET, algorithm=config.JWT_ALGORITMO)


def usuario_actual(token: str = Depends(oauth2)) -> dict:
    no_valido = HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado",
                              headers={"WWW-Authenticate": "Bearer"})
    try:
        datos = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITMO])
    except jwt.PyJWTError:
        raise no_valido
    return {"id": int(datos["sub"]), "usuario": datos["usuario"], "rol": datos["rol"]}


def solo_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    if usuario["rol"] != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Esta acción requiere el rol de administrador")
    return usuario
