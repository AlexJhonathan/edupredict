"""EduPredict API: servicio de IA para predecir el rendimiento académico."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .database import init_db
from .ml import servicio
from .routers import auth, datasets, modelo, predicciones

DESCRIPCION = """
API REST del sistema **EduPredict**. Estima la nota del examen final de un estudiante
(`Exam_Score`, 0-100) a partir de sus hábitos y su entorno, y marca en **riesgo** a quien
tenga una nota estimada menor a 65 para ofrecerle tutoría.

**Cómo probarla aquí:** pulsa *Authorize*, ingresa `admin` / `admin123` (o `docente` / `docente123`)
y luego usa cualquier endpoint.

* **Docente**: predecir, ver historial, métricas y monitoreo.
* **Administrador**: además sube archivos de entrenamiento, reentrena y activa versiones.
"""

TAGS = [
    {"name": "Autenticación", "description": "Inicio de sesión con JWT."},
    {"name": "Predicciones", "description": "Enviar datos al modelo y consultar el historial."},
    {"name": "Modelo", "description": "Métricas, versiones, monitoreo y reentrenamiento."},
    {"name": "Datos de entrenamiento", "description": "Subir y listar archivos CSV de entrenamiento."},
    {"name": "Sistema", "description": "Estado del servicio."},
]


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    init_db()
    servicio.asegurar_modelo_inicial()
    yield


app = FastAPI(title="EduPredict API", version="1.0.0", description=DESCRIPCION, openapi_tags=TAGS,
              lifespan=ciclo_de_vida, contact={"name": "Alex Jhonathan Choque Olguera"})

# CORS: el frontend corre en otro origen (otro puerto), así que se autorizan sus orígenes
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["GET", "POST", "PUT", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type"],
                   expose_headers=["Content-Disposition"])

for r in (auth.router, predicciones.router, modelo.router, datasets.router):
    app.include_router(r)


@app.get("/api/salud", tags=["Sistema"], summary="Estado del servicio y del modelo activo")
def salud():
    m = servicio.modelo_activo()["fila"]
    return {"estado": "ok", "modelo_activo": m["version"], "mae": round(m["mae"], 4)}
