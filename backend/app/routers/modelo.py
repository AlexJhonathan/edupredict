import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ..database import get_db
from ..ml import servicio
from ..ml.entrenamiento import verificar_requisitos
from ..ml.esquema import CATEGORICAS, NOTA_RIESGO, NUMERICAS, VARIABLES
from ..schemas import Entrenamiento, MetricasRespuesta, ModeloInfo, ReentrenarSolicitud
from ..security import solo_admin, usuario_actual

router = APIRouter(prefix="/api/modelo", tags=["Modelo"])


def _modelo(fila) -> dict:
    d = dict(fila)
    d["hiperparametros"] = json.loads(d["hiperparametros"])
    d["cumple_requisitos"] = bool(d["cumple_requisitos"])
    d.pop("referencia", None)
    d.pop("ruta_archivo", None)
    return d


_SELECT_ENTRENAMIENTO = """SELECT e.id, e.estado, e.dataset_id, e.incluir_notas_reales, e.modelo_id, e.mensaje,
                                  e.iniciado_en, e.finalizado_en, m.version AS modelo_version,
                                  u.usuario AS solicitado_por
                           FROM entrenamientos e LEFT JOIN modelos m ON m.id = e.modelo_id
                           LEFT JOIN usuarios u ON u.id = e.solicitado_por"""


def _entrenamiento(fila) -> dict:
    d = dict(fila)
    d["incluir_notas_reales"] = bool(d["incluir_notas_reales"])
    return d


@router.get("/metricas", response_model=MetricasRespuesta,
            summary="Métricas de rendimiento del modelo activo (test y producción)")
def metricas(_=Depends(usuario_actual), db=Depends(get_db)):
    fila = db.execute("SELECT * FROM modelos WHERE estado = 'activo'").fetchone()
    m = _modelo(fila)
    return {"modelo": m, "requisitos": verificar_requisitos(m), "produccion": servicio.metricas_produccion()}


@router.get("/versiones", response_model=list[ModeloInfo], summary="Todas las versiones del modelo")
def versiones(_=Depends(usuario_actual), db=Depends(get_db)):
    return [_modelo(f) for f in db.execute("SELECT * FROM modelos ORDER BY id DESC").fetchall()]


@router.post("/versiones/{modelo_id}/activar", response_model=ModeloInfo,
             summary="Activar una versión anterior (volver atrás)")
def activar(modelo_id: int, _=Depends(solo_admin)):
    try:
        return _modelo(servicio.activar_version(modelo_id))
    except LookupError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


@router.get("/contrato", summary="Variables de entrada y valores permitidos")
def contrato(_=Depends(usuario_actual)):
    ref = json.loads(servicio.modelo_activo()["fila"]["referencia"])["numericas"]
    campos = {}
    for v in VARIABLES:
        if v in NUMERICAS:
            campos[v] = {"tipo": "entero", "minimo": NUMERICAS[v][0], "maximo": NUMERICAS[v][1],
                         "min_entrenamiento": ref[v]["min"], "max_entrenamiento": ref[v]["max"]}
        else:
            campos[v] = {"tipo": "categoria", "valores": CATEGORICAS[v]}
    return {"campos": campos, "umbral_riesgo": NOTA_RIESGO, "objetivo": "Exam_Score"}


@router.get("/monitoreo", summary="Drift de los datos recibidos frente a los de entrenamiento (PSI)")
def monitoreo(_=Depends(usuario_actual)):
    return servicio.monitoreo()


@router.post("/reentrenar", response_model=Entrenamiento, status_code=status.HTTP_202_ACCEPTED,
             summary="Solicitar el reentrenamiento del modelo con información actualizada")
def reentrenar(solicitud: ReentrenarSolicitud, tareas: BackgroundTasks, usuario=Depends(solo_admin),
               db=Depends(get_db)):
    if db.execute("SELECT 1 FROM entrenamientos WHERE estado IN ('pendiente', 'en_progreso')").fetchone():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya hay un reentrenamiento en curso")
    dataset_id = solicitud.dataset_id
    if dataset_id is None:
        dataset_id = db.execute("SELECT id FROM datasets ORDER BY id DESC LIMIT 1").fetchone()[0]
    elif db.execute("SELECT 1 FROM datasets WHERE id = ?", (dataset_id,)).fetchone() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dataset no encontrado")
    cur = db.execute("INSERT INTO entrenamientos (solicitado_por, dataset_id, incluir_notas_reales, estado) "
                     "VALUES (?, ?, ?, 'pendiente')", (usuario["id"], dataset_id, int(solicitud.incluir_notas_reales)))
    db.commit()
    tareas.add_task(servicio.ejecutar_reentrenamiento, cur.lastrowid)
    return _entrenamiento(db.execute(f"{_SELECT_ENTRENAMIENTO} WHERE e.id = ?", (cur.lastrowid,)).fetchone())


@router.get("/entrenamientos", response_model=list[Entrenamiento], summary="Historial de entrenamientos")
def entrenamientos(_=Depends(usuario_actual), db=Depends(get_db)):
    return [_entrenamiento(f) for f in db.execute(f"{_SELECT_ENTRENAMIENTO} ORDER BY e.id DESC").fetchall()]


@router.get("/entrenamientos/{entrenamiento_id}", response_model=Entrenamiento,
            summary="Estado de un reentrenamiento")
def entrenamiento(entrenamiento_id: int, _=Depends(usuario_actual), db=Depends(get_db)):
    fila = db.execute(f"{_SELECT_ENTRENAMIENTO} WHERE e.id = ?", (entrenamiento_id,)).fetchone()
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrenamiento no encontrado")
    return _entrenamiento(fila)
