import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from .. import config
from ..database import get_db
from ..ml import servicio
from ..ml.esquema import TARGET, VARIABLES
from ..schemas import Dataset, DatasetSubido
from ..security import solo_admin, usuario_actual

router = APIRouter(prefix="/api/datasets", tags=["Datos de entrenamiento"])

_SELECT = """SELECT d.id, d.nombre_archivo, d.filas, d.filas_validas, d.origen, d.creado_en,
                    u.usuario AS subido_por
             FROM datasets d LEFT JOIN usuarios u ON u.id = d.subido_por"""


@router.post("", response_model=DatasetSubido, status_code=status.HTTP_201_CREATED,
             summary="Enviar un archivo CSV de entrenamiento")
async def subir(archivo: UploadFile = File(..., description="CSV con las 18 variables y Exam_Score"),
                usuario=Depends(solo_admin), db=Depends(get_db)):
    if not (archivo.filename or "").lower().endswith(".csv"):
        raise HTTPException(415, "El archivo debe ser .csv")
    limite = int(config.MAX_UPLOAD_MB * 1024 * 1024)
    contenido = await archivo.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(413, f"El archivo supera {config.MAX_UPLOAD_MB:g} MB")
    try:
        dataset, validacion = servicio.registrar_dataset(contenido, archivo.filename, "subido", usuario["id"])
    except ValueError as e:
        raise HTTPException(422, str(e))
    except FileExistsError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Este archivo ya fue subido (dataset {e.args[0]['id']})")
    if dataset is None:
        raise HTTPException(422,
                            {"mensaje": "El archivo no es válido para entrenar", "validacion": validacion})
    fila = db.execute(f"{_SELECT} WHERE d.id = ?", (dataset["id"],)).fetchone()
    return {"dataset": dict(fila), "validacion": validacion}


@router.get("", response_model=list[Dataset], summary="Archivos de entrenamiento registrados")
def listar(_=Depends(usuario_actual), db=Depends(get_db)):
    return [dict(f) for f in db.execute(f"{_SELECT} ORDER BY d.id DESC").fetchall()]


@router.get("/plantilla", summary="Descargar una plantilla CSV con las columnas requeridas")
def plantilla(_=Depends(usuario_actual)):
    ejemplo = pd.read_csv(config.DATASET_INICIAL, nrows=3)[VARIABLES + [TARGET]]
    buffer = io.StringIO()
    ejemplo.to_csv(buffer, index=False)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=plantilla_entrenamiento.csv"})
