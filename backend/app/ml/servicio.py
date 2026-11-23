"""Gestión del modelo activo: carga, predicción, reentrenamiento y monitoreo (Fases 5 y 6)."""
import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .. import config
from ..database import conexion
from .entrenamiento import entrenar, evaluar, limpiar, verificar_requisitos
from .esquema import CATEGORICAS, NOTA_RIESGO, NUMERICAS, TARGET, VARIABLES, columna_sql

_lock = threading.Lock()
_cache: dict = {}


def _ahora() -> str:
    # mismo formato y zona (UTC) que datetime('now') de SQLite
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- modelo activo
def modelo_activo() -> dict:
    """Devuelve el modelo activo (artefacto + fila de la tabla modelos), cargándolo una sola vez."""
    with _lock:
        with conexion() as con:
            fila = con.execute("SELECT * FROM modelos WHERE estado = 'activo'").fetchone()
        if fila is None:
            raise RuntimeError("No hay un modelo activo")
        if _cache.get("id") != fila["id"]:
            artefacto = joblib.load(config.STORAGE_DIR / fila["ruta_archivo"])
            _cache.clear()
            _cache.update({"id": fila["id"], "fila": dict(fila), **artefacto})
        return _cache


def _explicar(art: dict, X: pd.DataFrame) -> tuple[list, list]:
    """Aporte de cada variable frente a un estudiante promedio (el modelo es lineal)."""
    pipeline = art["pipeline"]
    x = np.asarray(pipeline.named_steps["prep"].transform(X)).ravel()
    aportes_t = pipeline.named_steps["modelo"].coef_ * (x - np.asarray(art["media_transformada"]))
    aportes: dict[str, float] = {}
    for nombre, valor in zip(art["nombres_transformados"], aportes_t):
        variable = nombre.split("__", 1)[1]
        variable = next((v for v in VARIABLES if variable == v or variable.startswith(v + "_")), variable)
        aportes[variable] = aportes.get(variable, 0.0) + float(valor)
    orden = sorted(aportes.items(), key=lambda kv: kv[1])
    a_favor = [{"variable": v, "aporte": round(a, 2)} for v, a in reversed(orden) if a > 0.05][:3]
    en_contra = [{"variable": v, "aporte": round(a, 2)} for v, a in orden if a < -0.05][:3]
    return a_favor, en_contra


def predecir(datos: dict) -> dict:
    art = modelo_activo()
    X = pd.DataFrame([{v: datos[v] for v in VARIABLES}])
    nota = float(np.clip(art["pipeline"].predict(X)[0], 0, 100))
    a_favor, en_contra = _explicar(art, X)

    advertencias = []
    ref = json.loads(art["fila"]["referencia"])["numericas"]
    for col in NUMERICAS:
        lo, hi = ref[col]["min"], ref[col]["max"]
        if not lo <= datos[col] <= hi:
            advertencias.append(f"{col} = {datos[col]} está fuera del rango visto en el entrenamiento "
                                f"({lo:g}-{hi:g}); la estimación es menos confiable")
    return {"nota_estimada": round(nota, 2), "riesgo": nota < NOTA_RIESGO, "modelo_id": art["id"],
            "modelo_version": art["fila"]["version"], "factores_a_favor": a_favor,
            "factores_en_contra": en_contra, "advertencias": advertencias}


# ---------------------------------------------------------------- datasets
def registrar_dataset(contenido: bytes, nombre: str, origen: str, usuario_id: int | None) -> tuple[dict, dict]:
    """Valida un CSV, lo guarda en storage/datasets y lo registra en la base de datos."""
    import io
    try:
        df = pd.read_csv(io.BytesIO(contenido))
    except Exception as e:  # archivo que no es CSV
        raise ValueError(f"No se pudo leer el archivo como CSV: {e}")
    _, reporte = limpiar(df)
    if not reporte.es_valido:
        return None, reporte.como_dict()

    sha = hashlib.sha256(contenido).hexdigest()
    with conexion() as con:
        existente = con.execute("SELECT * FROM datasets WHERE sha256 = ?", (sha,)).fetchone()
        if existente:
            raise FileExistsError(dict(existente))
        nombre_seguro = "".join(c for c in Path(nombre).stem if c.isalnum() or c in "-_")[:60] or "dataset"
        ruta = config.DATASETS_DIR / f"{sha[:12]}_{nombre_seguro}.csv"
        ruta.write_bytes(contenido)
        cur = con.execute(
            "INSERT INTO datasets (nombre_archivo, ruta, sha256, filas, filas_validas, origen, subido_por) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nombre, ruta.relative_to(config.STORAGE_DIR).as_posix(), sha, reporte.filas, reporte.filas_validas,
             origen, usuario_id))
        fila = con.execute("SELECT * FROM datasets WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(fila), reporte.como_dict()


def _cargar_dataset(dataset_id: int, incluir_notas_reales: bool) -> pd.DataFrame:
    with conexion() as con:
        fila = con.execute("SELECT ruta FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
        df = pd.read_csv(config.STORAGE_DIR / fila["ruta"])
        if incluir_notas_reales:
            cols = ", ".join(f"{columna_sql(v)} AS {v}" for v in VARIABLES)
            reales = pd.read_sql_query(
                f"SELECT {cols}, nota_real AS {TARGET} FROM predicciones WHERE nota_real IS NOT NULL", con)
            df = pd.concat([df, reales], ignore_index=True)
    limpio, _ = limpiar(df)
    return limpio


# ---------------------------------------------------------------- entrenamiento y versiones
def _guardar_version(con, res, dataset_id: int, estado: str) -> int:
    version_n = con.execute("SELECT COUNT(*) FROM modelos").fetchone()[0] + 1
    version = f"v{version_n}"
    ruta = config.MODELOS_DIR / f"modelo_{version}.joblib"
    joblib.dump({"pipeline": res.pipeline, "media_transformada": res.media_transformada,
                 "nombres_transformados": list(res.pipeline.named_steps["prep"].get_feature_names_out())}, ruta)
    m = res.metricas
    cumple = all(r["cumple"] for r in verificar_requisitos(m))
    cur = con.execute(
        """INSERT INTO modelos (version, algoritmo, hiperparametros, ruta_archivo, dataset_id, filas_entrenamiento,
           filas_test, mae, rmse, r2, recall_riesgo, precision_riesgo, mae_base, cumple_requisitos, estado, referencia)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (version, "HuberRegressor", json.dumps(res.parametros), ruta.relative_to(config.STORAGE_DIR).as_posix(),
         dataset_id, res.filas_train, len(res.y_test), m["mae"], m["rmse"], m["r2"], m["recall_riesgo"],
         m["precision_riesgo"], m["mae_base"], int(cumple), estado, json.dumps(res.referencia)))
    return cur.lastrowid


def asegurar_modelo_inicial() -> None:
    """Si la base está vacía, registra el dataset inicial y entrena el modelo v1 (igual al del notebook)."""
    with conexion() as con:
        if con.execute("SELECT COUNT(*) FROM modelos").fetchone()[0]:
            return
    contenido = config.DATASET_INICIAL.read_bytes()
    try:
        dataset, _ = registrar_dataset(contenido, config.DATASET_INICIAL.name, "inicial", None)
    except FileExistsError as e:
        dataset = e.args[0]
    df, _ = limpiar(pd.read_csv(config.DATASET_INICIAL))
    res = entrenar(df, buscar_hiperparametros=False, seed=config.SEED)
    with conexion() as con:
        modelo_id = _guardar_version(con, res, dataset["id"], "activo")
        con.execute(
            "INSERT INTO entrenamientos (dataset_id, estado, modelo_id, mensaje, finalizado_en) VALUES (?, ?, ?, ?, ?)",
            (dataset["id"], "completado", modelo_id, "Entrenamiento inicial con los hiperparámetros de la Fase 3",
             _ahora()))


def ejecutar_reentrenamiento(entrenamiento_id: int) -> None:
    """Tarea en segundo plano: entrena un modelo retador y lo activa solo si mejora al actual."""
    with conexion() as con:
        job = dict(con.execute("SELECT * FROM entrenamientos WHERE id = ?", (entrenamiento_id,)).fetchone())
        con.execute("UPDATE entrenamientos SET estado = 'en_progreso' WHERE id = ?", (entrenamiento_id,))
    try:
        df = _cargar_dataset(job["dataset_id"], bool(job["incluir_notas_reales"]))
        if len(df) < 200:
            raise ValueError("No hay suficientes filas válidas para entrenar")
        res = entrenar(df, buscar_hiperparametros=True, seed=config.SEED)

        # el modelo actual se evalúa en el mismo test para comparar en igualdad de condiciones
        actual = modelo_activo()
        m_actual = evaluar(actual["pipeline"], res.X_test, res.y_test, res.metricas["mae_base"])
        cumple = all(r["cumple"] for r in verificar_requisitos(res.metricas))
        mejora = res.metricas["mae"] <= m_actual["mae"]
        promover = cumple and mejora

        with conexion() as con:
            if promover:
                con.execute("UPDATE modelos SET estado = 'archivado' WHERE estado = 'activo'")
            modelo_id = _guardar_version(con, res, job["dataset_id"], "activo" if promover else "rechazado")
            version = con.execute("SELECT version FROM modelos WHERE id = ?", (modelo_id,)).fetchone()[0]
            if promover:
                mensaje = (f"{version} activado: MAE {res.metricas['mae']:.3f} frente a "
                           f"{m_actual['mae']:.3f} del modelo {actual['fila']['version']} en el mismo test")
            elif not cumple:
                mensaje = f"{version} rechazado: no cumple los requisitos de aceptación"
            else:
                mensaje = (f"{version} rechazado: MAE {res.metricas['mae']:.3f} no mejora el "
                           f"{m_actual['mae']:.3f} del modelo {actual['fila']['version']}")
            con.execute("UPDATE entrenamientos SET estado = 'completado', modelo_id = ?, mensaje = ?, "
                        "finalizado_en = ? WHERE id = ?", (modelo_id, mensaje, _ahora(), entrenamiento_id))
    except Exception as e:
        with conexion() as con:
            con.execute("UPDATE entrenamientos SET estado = 'fallido', mensaje = ?, finalizado_en = ? WHERE id = ?",
                        (str(e)[:500], _ahora(), entrenamiento_id))


def activar_version(modelo_id: int) -> dict:
    with conexion() as con:
        fila = con.execute("SELECT * FROM modelos WHERE id = ?", (modelo_id,)).fetchone()
        if fila is None:
            raise LookupError("Versión no encontrada")
        if not fila["cumple_requisitos"]:
            raise ValueError("Solo se pueden activar versiones que cumplen los requisitos de aceptación")
        con.execute("UPDATE modelos SET estado = 'archivado' WHERE estado = 'activo'")
        con.execute("UPDATE modelos SET estado = 'activo' WHERE id = ?", (modelo_id,))
        return dict(con.execute("SELECT * FROM modelos WHERE id = ?", (modelo_id,)).fetchone())


# ---------------------------------------------------------------- monitoreo (Fase 6)
def _psi(esperado: np.ndarray, actual: np.ndarray) -> float:
    e, a = np.clip(esperado, 1e-4, None), np.clip(actual, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


def monitoreo(min_predicciones: int = 30) -> dict:
    art = modelo_activo()
    ref = json.loads(art["fila"]["referencia"])
    with conexion() as con:
        cols = ", ".join(f"{columna_sql(v)} AS {v}" for v in VARIABLES)
        df = pd.read_sql_query(f"SELECT {cols} FROM predicciones ORDER BY id DESC LIMIT 1000", con)
    resultado = {"modelo_version": art["fila"]["version"], "predicciones_analizadas": len(df),
                 "minimo_requerido": min_predicciones, "suficientes_datos": len(df) >= min_predicciones,
                 "variables": []}
    if len(df) < min_predicciones:
        return resultado
    for col, r in ref["numericas"].items():
        cortes = np.array(r["cortes"])
        conteo = np.histogram(np.clip(df[col], cortes[0], cortes[-1]), cortes)[0]
        resultado["variables"].append({"variable": col, "tipo": "numérica",
                                       "psi": _psi(np.array(r["proporciones"]), conteo / conteo.sum())})
    for col, r in ref["categoricas"].items():
        prop = df[col].value_counts(normalize=True)
        resultado["variables"].append({"variable": col, "tipo": "categórica",
                                       "psi": _psi(np.array(list(r.values())), np.array([prop.get(v, 0.0) for v in r]))})
    for v in resultado["variables"]:
        v["psi"] = round(v["psi"], 4)
        v["estado"] = "alto" if v["psi"] > 0.2 else "moderado" if v["psi"] > 0.1 else "estable"
    resultado["variables"].sort(key=lambda v: -v["psi"])
    resultado["alertas"] = sum(v["estado"] == "alto" for v in resultado["variables"])
    return resultado


def metricas_produccion() -> dict:
    with conexion() as con:
        f = con.execute("""SELECT COUNT(*) AS total, SUM(riesgo) AS en_riesgo,
                                  SUM(nota_real IS NOT NULL) AS con_nota_real FROM predicciones""").fetchone()
        reales = con.execute("SELECT nota_estimada, nota_real FROM predicciones WHERE nota_real IS NOT NULL").fetchall()
    total = f["total"] or 0
    salida = {"predicciones": total, "en_riesgo": f["en_riesgo"] or 0,
              "porcentaje_riesgo": round((f["en_riesgo"] or 0) / total, 4) if total else 0.0,
              "con_nota_real": f["con_nota_real"] or 0, "mae_real": None, "recall_riesgo_real": None}
    if reales:
        est = np.array([r[0] for r in reales]); real = np.array([r[1] for r in reales])
        salida["mae_real"] = round(float(np.mean(np.abs(est - real))), 4)
        en_riesgo = real < NOTA_RIESGO
        if en_riesgo.any():
            salida["recall_riesgo_real"] = round(float(((est < NOTA_RIESGO) & en_riesgo).sum() / en_riesgo.sum()), 4)
    return salida


def limpiar_cache() -> None:
    with _lock:
        _cache.clear()
