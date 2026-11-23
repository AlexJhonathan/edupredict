-- =============================================================
--  EduPredict - Esquema de la base de datos (SQLite)
--  Se ejecuta automáticamente al iniciar la API (app/database.py)
--  o manualmente con:  python scripts/init_db.py
--  o con la consola de SQLite:  sqlite3 storage/edupredict.db < db/schema.sql
-- =============================================================

PRAGMA foreign_keys = ON;

-- Usuarios que consumen la API (docentes y administradores)
CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario         TEXT    NOT NULL UNIQUE,
    nombre          TEXT    NOT NULL,
    password_hash   TEXT    NOT NULL,
    rol             TEXT    NOT NULL CHECK (rol IN ('admin', 'docente')),
    activo          INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Archivos de entrenamiento (el dataset inicial y los que se suben por la API)
CREATE TABLE IF NOT EXISTS datasets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_archivo  TEXT    NOT NULL,
    ruta            TEXT    NOT NULL,
    sha256          TEXT    NOT NULL UNIQUE,
    filas           INTEGER NOT NULL,
    filas_validas   INTEGER NOT NULL,
    origen          TEXT    NOT NULL CHECK (origen IN ('inicial', 'subido')),
    subido_por      INTEGER REFERENCES usuarios(id),
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Versiones del modelo y sus métricas en el conjunto de test
CREATE TABLE IF NOT EXISTS modelos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    version             TEXT    NOT NULL UNIQUE,
    algoritmo           TEXT    NOT NULL,
    hiperparametros     TEXT    NOT NULL,              -- JSON
    ruta_archivo        TEXT    NOT NULL,
    dataset_id          INTEGER NOT NULL REFERENCES datasets(id),
    filas_entrenamiento INTEGER NOT NULL,
    filas_test          INTEGER NOT NULL,
    mae                 REAL    NOT NULL,
    rmse                REAL    NOT NULL,
    r2                  REAL    NOT NULL,
    recall_riesgo       REAL    NOT NULL,
    precision_riesgo    REAL    NOT NULL,
    mae_base            REAL    NOT NULL,
    cumple_requisitos   INTEGER NOT NULL CHECK (cumple_requisitos IN (0, 1)),
    estado              TEXT    NOT NULL CHECK (estado IN ('activo', 'archivado', 'rechazado')),
    referencia          TEXT    NOT NULL,              -- JSON: distribución de entrenamiento para monitorear drift
    creado_en           TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Solicitudes de reentrenamiento y su resultado
CREATE TABLE IF NOT EXISTS entrenamientos (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitado_por          INTEGER REFERENCES usuarios(id),
    dataset_id              INTEGER NOT NULL REFERENCES datasets(id),
    incluir_notas_reales    INTEGER NOT NULL DEFAULT 0 CHECK (incluir_notas_reales IN (0, 1)),
    estado                  TEXT    NOT NULL CHECK (estado IN ('pendiente', 'en_progreso', 'completado', 'fallido')),
    modelo_id               INTEGER REFERENCES modelos(id),
    mensaje                 TEXT,
    iniciado_en             TEXT    NOT NULL DEFAULT (datetime('now')),
    finalizado_en           TEXT
);

-- Historial de predicciones: datos enviados, resultado y, si se conoce, la nota real
CREATE TABLE IF NOT EXISTS predicciones (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id                   INTEGER NOT NULL REFERENCES modelos(id),
    usuario_id                  INTEGER NOT NULL REFERENCES usuarios(id),
    codigo_estudiante           TEXT,
    hours_studied               INTEGER NOT NULL,
    attendance                  INTEGER NOT NULL,
    parental_involvement        TEXT    NOT NULL,
    access_to_resources         TEXT    NOT NULL,
    extracurricular_activities  TEXT    NOT NULL,
    sleep_hours                 INTEGER NOT NULL,
    previous_scores             INTEGER NOT NULL,
    motivation_level            TEXT    NOT NULL,
    internet_access             TEXT    NOT NULL,
    tutoring_sessions           INTEGER NOT NULL,
    family_income               TEXT    NOT NULL,
    teacher_quality             TEXT    NOT NULL,
    school_type                 TEXT    NOT NULL,
    peer_influence              TEXT    NOT NULL,
    physical_activity           INTEGER NOT NULL,
    learning_disabilities       TEXT    NOT NULL,
    parental_education_level    TEXT    NOT NULL,
    distance_from_home          TEXT    NOT NULL,
    nota_estimada               REAL    NOT NULL,
    riesgo                      INTEGER NOT NULL CHECK (riesgo IN (0, 1)),
    nota_real                   REAL CHECK (nota_real IS NULL OR (nota_real >= 0 AND nota_real <= 100)),
    creado_en                   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_predicciones_fecha  ON predicciones (creado_en);
CREATE INDEX IF NOT EXISTS idx_predicciones_riesgo ON predicciones (riesgo);
CREATE INDEX IF NOT EXISTS idx_predicciones_modelo ON predicciones (modelo_id);
CREATE INDEX IF NOT EXISTS idx_modelos_estado      ON modelos (estado);
