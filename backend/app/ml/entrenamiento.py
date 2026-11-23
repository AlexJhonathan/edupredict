"""Limpieza, entrenamiento y evaluación del modelo (Fases 2, 3 y 4 de CRISP-ML(Q)).

Reproduce lo que se hizo en el notebook de ciencia de datos para que el reentrenamiento
desde la API siga exactamente el mismo proceso.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from .esquema import (BINARIAS, CATEGORICAS, GRILLA_REENTRENAMIENTO, MIN_FILAS_ENTRENAMIENTO,
                      NOTA_RIESGO, NUMERICAS, ORDINALES, REQUISITOS, TARGET, VARIABLES)


# ---------------------------------------------------------------- limpieza (Fase 2)
@dataclass
class ReporteValidacion:
    filas: int = 0
    filas_validas: int = 0
    columnas_faltantes: list = field(default_factory=list)
    advertencias: list = field(default_factory=list)

    @property
    def es_valido(self) -> bool:
        return not self.columnas_faltantes and self.filas_validas >= MIN_FILAS_ENTRENAMIENTO

    def como_dict(self) -> dict:
        return {"filas": self.filas, "filas_validas": self.filas_validas,
                "columnas_faltantes": self.columnas_faltantes, "advertencias": self.advertencias,
                "es_valido": self.es_valido}


def limpiar(df: pd.DataFrame) -> tuple[pd.DataFrame, ReporteValidacion]:
    """Valida un archivo de entrenamiento y devuelve solo las filas utilizables."""
    rep = ReporteValidacion(filas=len(df))
    rep.columnas_faltantes = [c for c in VARIABLES + [TARGET] if c not in df.columns]
    if rep.columnas_faltantes:
        return df.iloc[0:0], rep

    df = df[VARIABLES + [TARGET]].copy()

    # la nota debe existir y estar entre 0 y 100
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    malas = df[TARGET].isna() | (df[TARGET] < 0) | (df[TARGET] > 100)
    if malas.any():
        rep.advertencias.append(f"{int(malas.sum())} filas con Exam_Score vacío o fuera de 0-100 fueron descartadas")
    df = df[~malas]

    # numéricas dentro de su rango
    for col, (lo, hi) in NUMERICAS.items():
        df[col] = pd.to_numeric(df[col], errors="coerce")
        fuera = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        if fuera.any():
            rep.advertencias.append(f"{int(fuera.sum())} filas con {col} fuera de {lo}-{hi} fueron descartadas")
            df = df[~fuera]
        vacias = df[col].isna().sum()
        if vacias:
            rep.advertencias.append(f"{int(vacias)} valores vacíos en {col} se completarán con la mediana")

    # categorías desconocidas se tratan como vacías y se imputan con la moda
    for col, valores in CATEGORICAS.items():
        df[col] = df[col].astype("string").str.strip()
        desconocidas = df[col].notna() & ~df[col].isin(valores)
        if desconocidas.any():
            rep.advertencias.append(f"{int(desconocidas.sum())} valores no reconocidos en {col} se completarán con la moda")
            df.loc[desconocidas, col] = pd.NA
        df[col] = df[col].astype(object).where(df[col].notna(), np.nan)

    rep.filas_validas = len(df)
    if rep.filas_validas < MIN_FILAS_ENTRENAMIENTO:
        rep.advertencias.append(f"Se necesitan al menos {MIN_FILAS_ENTRENAMIENTO} filas válidas para entrenar")
    return df.reset_index(drop=True), rep


# ---------------------------------------------------------------- pipeline
def construir_pipeline(epsilon: float = 2.0, alpha: float = 3.0) -> Pipeline:
    num = list(NUMERICAS)
    prep = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("esc", StandardScaler())]), num),
        ("ord", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("enc", OrdinalEncoder(categories=list(ORDINALES.values()),
                                                 handle_unknown="use_encoded_value", unknown_value=np.nan)),
                          ("imp2", SimpleImputer(strategy="most_frequent"))]), list(ORDINALES)),
        ("bin", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("ohe", OneHotEncoder(categories=list(BINARIAS.values()), drop="first",
                                                handle_unknown="ignore"))]), list(BINARIAS)),
    ])
    return Pipeline([("prep", prep), ("modelo", HuberRegressor(epsilon=epsilon, alpha=alpha, max_iter=2000))])


# ---------------------------------------------------------------- evaluación (Fase 4)
def evaluar(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series, mae_base: float) -> dict:
    pred = np.clip(pipeline.predict(X), 0, 100)
    real_riesgo, marcado = y.values < NOTA_RIESGO, pred < NOTA_RIESGO
    tp = int((real_riesgo & marcado).sum())
    mae = float(mean_absolute_error(y, pred))
    return {
        "mae": mae,
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
        "r2": float(r2_score(y, pred)),
        "recall_riesgo": tp / real_riesgo.sum() if real_riesgo.sum() else 0.0,
        "precision_riesgo": tp / marcado.sum() if marcado.sum() else 0.0,
        "mae_base": float(mae_base),
    }


def verificar_requisitos(m: dict) -> list[dict]:
    mejora = 1 - m["mae"] / m["mae_base"] if m["mae_base"] else 0.0
    filas = [
        ("MAE (puntos)", m["mae"], f"<= {REQUISITOS['mae_max']}", m["mae"] <= REQUISITOS["mae_max"]),
        ("Mejora frente al modelo base", mejora, f">= {REQUISITOS['mejora_vs_base_min']:.0%}",
         mejora >= REQUISITOS["mejora_vs_base_min"]),
        ("R²", m["r2"], f">= {REQUISITOS['r2_min']}", m["r2"] >= REQUISITOS["r2_min"]),
        ("Recall de riesgo", m["recall_riesgo"], f">= {REQUISITOS['recall_riesgo_min']}",
         m["recall_riesgo"] >= REQUISITOS["recall_riesgo_min"]),
        ("Precisión de riesgo", m["precision_riesgo"], f">= {REQUISITOS['precision_riesgo_min']}",
         m["precision_riesgo"] >= REQUISITOS["precision_riesgo_min"]),
    ]
    return [{"metrica": n, "valor": round(float(v), 4), "umbral": u, "cumple": bool(c)} for n, v, u, c in filas]


# ---------------------------------------------------------------- referencia para monitoreo (Fase 6)
def distribucion_referencia(X: pd.DataFrame) -> dict:
    ref = {"numericas": {}, "categoricas": {}}
    for col in NUMERICAS:
        cortes = np.unique(np.quantile(X[col].dropna(), np.linspace(0, 1, 11)))
        conteo = np.histogram(X[col].dropna(), cortes)[0]
        ref["numericas"][col] = {"cortes": cortes.tolist(), "proporciones": (conteo / conteo.sum()).tolist(),
                                 "min": float(X[col].min()), "max": float(X[col].max())}
    for col, valores in CATEGORICAS.items():
        prop = X[col].value_counts(normalize=True)
        ref["categoricas"][col] = {v: float(prop.get(v, 0.0)) for v in valores}
    return ref


# ---------------------------------------------------------------- entrenamiento (Fase 3)
@dataclass
class Resultado:
    pipeline: Pipeline
    parametros: dict
    metricas: dict
    X_test: pd.DataFrame
    y_test: pd.Series
    filas_train: int
    referencia: dict
    media_transformada: list


def entrenar(df: pd.DataFrame, buscar_hiperparametros: bool = True, seed: int = 42) -> Resultado:
    """Divide 80/20 (estratificado por riesgo), entrena Huber y evalúa en el test."""
    X, y = df[VARIABLES], df[TARGET].astype(float)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=seed, stratify=(y < NOTA_RIESGO))

    if buscar_hiperparametros:
        busqueda = GridSearchCV(construir_pipeline(), GRILLA_REENTRENAMIENTO, scoring="neg_mean_absolute_error",
                                cv=KFold(5, shuffle=True, random_state=seed), n_jobs=-1).fit(X_train, y_train)
        pipeline = busqueda.best_estimator_
        parametros = {k.replace("modelo__", ""): float(v) for k, v in busqueda.best_params_.items()}
    else:
        from .esquema import PARAMETROS_INICIALES
        parametros = dict(PARAMETROS_INICIALES)
        pipeline = construir_pipeline(**parametros).fit(X_train, y_train)

    mae_base = mean_absolute_error(y_test, np.full(len(y_test), y_train.mean()))
    media = pipeline.named_steps["prep"].transform(X_train).mean(axis=0)
    return Resultado(pipeline=pipeline, parametros=parametros, metricas=evaluar(pipeline, X_test, y_test, mae_base),
                     X_test=X_test, y_test=y_test, filas_train=len(X_train),
                     referencia=distribucion_referencia(X_train), media_transformada=np.asarray(media).ravel().tolist())
