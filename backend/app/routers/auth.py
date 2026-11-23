from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..database import get_db
from ..schemas import Token, Usuario
from ..security import crear_token, usuario_actual, verificar_password

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token, summary="Iniciar sesión y obtener un token JWT")
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    fila = db.execute("SELECT * FROM usuarios WHERE usuario = ? AND activo = 1", (form.username,)).fetchone()
    if fila is None or not verificar_password(form.password, fila["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos")
    usuario = {k: fila[k] for k in ("id", "usuario", "nombre", "rol")}
    return {"access_token": crear_token(usuario), "token_type": "bearer", "usuario": usuario}


@router.get("/yo", response_model=Usuario, summary="Datos del usuario autenticado")
def yo(usuario=Depends(usuario_actual), db=Depends(get_db)):
    fila = db.execute("SELECT id, usuario, nombre, rol FROM usuarios WHERE id = ?", (usuario["id"],)).fetchone()
    return dict(fila)
