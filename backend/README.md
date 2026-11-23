# Backend · Servicio de IA de EduPredict

API REST hecha con **FastAPI** que expone el modelo de predicción del rendimiento académico.
Guarda las predicciones y las versiones del modelo en **SQLite**, permite subir archivos de
entrenamiento, reentrenar el modelo sin detener el servicio y monitorear el drift.

## Estructura

```
backend/
├── app/
│   ├── main.py            # aplicación, CORS y registro de rutas
│   ├── config.py          # configuración leída de .env
│   ├── database.py        # conexión SQLite y creación de tablas
│   ├── security.py        # contraseñas (bcrypt) y tokens JWT
│   ├── schemas.py         # validación de entradas y salidas (Pydantic)
│   ├── ml/
│   │   ├── esquema.py         # variables, valores permitidos y requisitos de aceptación
│   │   ├── entrenamiento.py   # limpieza, pipeline, entrenamiento y evaluación
│   │   └── servicio.py        # modelo activo, predicción, reentrenamiento y monitoreo
│   └── routers/           # auth, predicciones, modelo, datasets
├── db/schema.sql          # script de la base de datos
├── data/                  # dataset inicial
├── scripts/               # init_db, exportar_openapi, cargar_demo
├── tests/                 # pruebas automáticas (pytest)
└── storage/               # se crea al ejecutar: base de datos, modelos y CSV subidos
```

## Instalación y ejecución

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Swagger: http://localhost:8000/docs · ReDoc: http://localhost:8000/redoc

## Base de datos

Al arrancar, la API ejecuta `db/schema.sql` (con `CREATE TABLE IF NOT EXISTS`), crea los usuarios
de `.env` y, si no hay modelos, entrena el **v1** con el dataset de `data/`. También se puede hacer a mano:

```bash
python scripts/init_db.py
# o solo las tablas, con la consola de SQLite:
sqlite3 storage/edupredict.db < db/schema.sql
```

Para empezar de cero basta con borrar la carpeta `storage/`.

## Seguridad

- **JWT**: `POST /api/auth/login` devuelve un token que se envía como `Authorization: Bearer <token>`.
- **Roles**: `docente` puede predecir y consultar; `admin` además sube archivos, reentrena y activa versiones.
- **CORS**: solo se aceptan los orígenes de `CORS_ORIGINS` (por defecto el frontend en `http://localhost:5173`).

## Reentrenamiento

`POST /api/modelo/reentrenar` responde `202` y entrena en segundo plano un modelo **retador** con el dataset
elegido (más las predicciones que ya tienen nota real, si se pide). El retador se evalúa junto al modelo
activo en el mismo conjunto de test y **solo se activa si cumple los requisitos y su MAE es igual o menor**;
si no, queda como `rechazado`. El estado se consulta en `GET /api/modelo/entrenamientos/{id}`.

## Utilidades

```bash
python -m pytest -q                      # pruebas (requiere requirements-dev.txt)
python scripts/exportar_openapi.py       # actualiza docs/api/openapi.json y openapi.yaml
python scripts/cargar_demo.py            # carga predicciones de ejemplo (con la API encendida)
```
