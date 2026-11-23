"""Genera archivos SIMULADOS para demostrar la subida de datos y el reentrenamiento.

- semestre_2026_2_simulado.csv: 3.000 estudiantes del dataset original en los que se simula
  que un nuevo programa de tutorías es más efectivo (cada sesión suma 1 punto extra a la nota).
  Representa "información actualizada" con un cambio de concepto, para que el reentrenamiento
  produzca un modelo mejor que el anterior.
- archivo_incompleto_ejemplo.csv: archivo con columnas faltantes, para mostrar la validación.

Estos datos NO son reales: solo sirven para la demostración del sistema.
Uso (desde la carpeta ciencia-datos):  python scripts/generar_datos_demo.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE / "data" / "StudentPerformanceFactors.csv")
df = df[df["Exam_Score"] <= 100]

nuevo = df.sample(3000, random_state=2026).copy()
nuevo["Exam_Score"] = np.clip(nuevo["Exam_Score"] + nuevo["Tutoring_Sessions"] * 1.0, 0, 100).round().astype(int)

salida = BASE / "data" / "demo"
salida.mkdir(parents=True, exist_ok=True)
nuevo.to_csv(salida / "semestre_2026_2_simulado.csv", index=False)
df[["Hours_Studied", "Attendance", "Sleep_Hours"]].head(50).to_csv(salida / "archivo_incompleto_ejemplo.csv", index=False)
print("Archivos de demostración generados en", salida)
