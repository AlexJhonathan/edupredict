from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_db
from ..ml import servicio
from ..ml.esquema import NOTA_RIESGO, VARIABLES, columna_sql
from ..schemas import EstudianteEntrada, NotaReal, PaginaHistorial, PrediccionHistorial, PrediccionRespuesta
from ..security import usuario_actual

router = APIRouter(prefix="/api/predicciones", tags=["Predicciones"])

_SELECT = f"""SELECT p.*, m.version AS modelo_version, u.usuario AS usuario
              FROM predicciones p JOIN modelos m ON m.id = p.modelo_id JOIN usuarios u ON u.id = p.usuario_id"""


def _a_historial(fila) -> dict:
    return {"id": fila["id"], "creado_en": fila["creado_en"], "codigo_estudiante": fila["codigo_estudiante"],
            "entrada": {v: fila[columna_sql(v)] for v in VARIABLES}, "nota_estimada": fila["nota_estimada"],
            "riesgo": bool(fila["riesgo"]), "nota_real": fila["nota_real"],
            "modelo_version": fila["modelo_version"], "usuario": fila["usuario"]}


@router.post("", response_model=PrediccionRespuesta, status_code=status.HTTP_201_CREATED,
             summary="Enviar los datos de un estudiante y obtener la nota estimada")
def crear_prediccion(estudiante: EstudianteEntrada, usuario=Depends(usuario_actual), db=Depends(get_db)):
    datos = estudiante.model_dump()
    r = servicio.predecir(datos)
    columnas = ["modelo_id", "usuario_id", "codigo_estudiante"] + [columna_sql(v) for v in VARIABLES] + \
               ["nota_estimada", "riesgo"]
    valores = [r["modelo_id"], usuario["id"], datos.get("codigo_estudiante")] + [datos[v] for v in VARIABLES] + \
              [r["nota_estimada"], int(r["riesgo"])]
    cur = db.execute(f"INSERT INTO predicciones ({', '.join(columnas)}) VALUES ({', '.join('?' * len(valores))})",
                     valores)
    creado = db.execute("SELECT creado_en FROM predicciones WHERE id = ?", (cur.lastrowid,)).fetchone()[0]
    return {"id": cur.lastrowid, "umbral_riesgo": NOTA_RIESGO, "creado_en": creado,
            **{k: v for k, v in r.items() if k != "modelo_id"}}


@router.get("", response_model=PaginaHistorial, summary="Historial de predicciones: datos enviados y resultado")
def historial(pagina: int = Query(1, ge=1), tamano: int = Query(20, ge=1, le=200),
              riesgo: Optional[bool] = Query(None, description="Filtrar por estudiantes en riesgo"),
              codigo: Optional[str] = Query(None, description="Buscar por código de estudiante"),
              desde: Optional[str] = Query(None, description="Fecha inicial (AAAA-MM-DD)"),
              hasta: Optional[str] = Query(None, description="Fecha final (AAAA-MM-DD)"),
              _=Depends(usuario_actual), db=Depends(get_db)):
    filtros, params = [], []
    if riesgo is not None:
        filtros.append("p.riesgo = ?"); params.append(int(riesgo))
    if codigo:
        filtros.append("p.codigo_estudiante LIKE ?"); params.append(f"%{codigo}%")
    if desde:
        filtros.append("date(p.creado_en) >= date(?)"); params.append(desde)
    if hasta:
        filtros.append("date(p.creado_en) <= date(?)"); params.append(hasta)
    where = f" WHERE {' AND '.join(filtros)}" if filtros else ""
    total = db.execute(f"SELECT COUNT(*) FROM predicciones p{where}", params).fetchone()[0]
    filas = db.execute(f"{_SELECT}{where} ORDER BY p.id DESC LIMIT ? OFFSET ?",
                       params + [tamano, (pagina - 1) * tamano]).fetchall()
    return {"total": total, "pagina": pagina, "tamano": tamano, "items": [_a_historial(f) for f in filas]}


@router.get("/{prediccion_id}", response_model=PrediccionHistorial, summary="Detalle de una predicción")
def detalle(prediccion_id: int, _=Depends(usuario_actual), db=Depends(get_db)):
    fila = db.execute(f"{_SELECT} WHERE p.id = ?", (prediccion_id,)).fetchone()
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Predicción no encontrada")
    return _a_historial(fila)


@router.put("/{prediccion_id}/nota-real", response_model=PrediccionHistorial,
            summary="Registrar la nota real del examen (sirve para monitorear y reentrenar)")
def registrar_nota_real(prediccion_id: int, cuerpo: NotaReal, _=Depends(usuario_actual), db=Depends(get_db)):
    cur = db.execute("UPDATE predicciones SET nota_real = ? WHERE id = ?", (cuerpo.nota_real, prediccion_id))
    if cur.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Predicción no encontrada")
    return _a_historial(db.execute(f"{_SELECT} WHERE p.id = ?", (prediccion_id,)).fetchone())
