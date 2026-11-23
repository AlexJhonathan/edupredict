# Ciencia de datos · Fases 1 a 4 de CRISP-ML(Q)

Entrenamiento y validación del modelo que luego expone el servicio de IA.

- [`Proyecto_Final_CRISP_MLQ.ipynb`](Proyecto_Final_CRISP_MLQ.ipynb): notebook ejecutado con las fases
  1 (negocio y datos), 2 (ingeniería de datos), 3 (ingeniería del modelo) y 4 (evaluación y QA).
- `data/StudentPerformanceFactors.csv`: dataset de [Kaggle](https://www.kaggle.com/datasets/lainguyn123/student-performance-factors).
- `artefactos/`: figuras, datos versionados con su hash, modelo v1, metadatos, Model Card y contrato de entrada de la API.
- `data/demo/`: archivos **simulados** para la demostración (un semestre con un programa de tutorías más
  efectivo y un archivo incompleto). Se generan con `python scripts/generar_datos_demo.py`.

## Ejecutar el notebook

```bash
pip install -r requirements.txt
jupyter notebook Proyecto_Final_CRISP_MLQ.ipynb
```

## Resumen

| Decisión | Detalle |
|---|---|
| Objetivo | Estimar la nota del examen y marcar en riesgo a quien tenga menos de 65 |
| Métrica principal | MAE (en puntos de nota), más RMSE, R², recall y precisión de riesgo |
| Limpieza | Se elimina 1 nota de 101; faltantes imputados con la moda; `Gender` fuera del modelo |
| Modelo | Regresión de Huber (`epsilon = 2`, `alpha = 3`), mejor que lineal, árboles y boosting |
| Test | MAE 0,376 · R² 0,819 · recall de riesgo 1,00 · precisión de riesgo 0,81 |

El módulo `backend/app/ml` reproduce exactamente este proceso, por eso el modelo v1 de la API tiene las mismas métricas.
