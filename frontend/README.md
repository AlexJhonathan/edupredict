# Frontend · Aplicación web de EduPredict

Interfaz hecha con **React + Vite** que consume todos los endpoints del servicio de IA.
Es un proyecto independiente del backend: solo necesita la URL de la API.

## Pantallas

| Pantalla | Endpoints que usa |
|---|---|
| Inicio de sesión | `POST /api/auth/login` |
| Panel | `GET /api/salud`, `GET /api/modelo/metricas`, `GET /api/predicciones`, `GET /api/modelo/monitoreo` |
| Nueva predicción | `GET /api/modelo/contrato`, `POST /api/predicciones` |
| Historial | `GET /api/predicciones`, `GET /api/predicciones/{id}`, `PUT /api/predicciones/{id}/nota-real` |
| Modelo y métricas | `GET /api/modelo/metricas`, `GET /api/modelo/versiones`, `POST /api/modelo/versiones/{id}/activar`, `GET /api/modelo/monitoreo` |
| Datos y reentrenamiento | `POST /api/datasets`, `GET /api/datasets`, `GET /api/datasets/plantilla`, `POST /api/modelo/reentrenar`, `GET /api/modelo/entrenamientos`, `GET /api/modelo/entrenamientos/{id}` |

Todas las llamadas están en [`src/api.js`](src/api.js).

## Ejecución

Requiere Node.js 20.19 o superior.

```bash
npm install
cp .env.example .env       # VITE_API_URL=http://localhost:8000
npm run dev                # http://localhost:5173
```

Compilación para producción: `npm run build` (genera `dist/`). Si el frontend se publica en otro dominio,
agrega ese origen a `CORS_ORIGINS` en el `.env` del backend.

## Estructura

```
src/
├── api.js              # cliente de la API REST (fetch + token JWT)
├── auth.jsx            # sesión del usuario
├── App.jsx             # rutas
├── components/         # menú lateral, tarjetas, botones, modal, íconos
├── lib/                # etiquetas en español de las variables y formatos
├── pages/              # Login, Panel, Prediccion, Historial, Modelo, Datos
└── styles.css
```
