"""Carga predicciones de ejemplo a través de la API (útil para la demostración).

Toma estudiantes al azar del dataset, los envía a POST /api/predicciones y registra la nota
real de una parte de ellos con PUT /api/predicciones/{id}/nota-real.

Uso (con la API encendida):  python scripts/cargar_demo.py --cantidad 80
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

VARIABLES = ["Hours_Studied", "Attendance", "Parental_Involvement", "Access_to_Resources",
             "Extracurricular_Activities", "Sleep_Hours", "Previous_Scores", "Motivation_Level",
             "Internet_Access", "Tutoring_Sessions", "Family_Income", "Teacher_Quality", "School_Type",
             "Peer_Influence", "Physical_Activity", "Learning_Disabilities", "Parental_Education_Level",
             "Distance_from_Home"]


def pedir(url, metodo="GET", datos=None, token=None, form=False):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    cuerpo = None
    if datos is not None:
        if form:
            cuerpo = urllib.parse.urlencode(datos).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            cuerpo = json.dumps(datos).encode()
            headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=cuerpo, headers=headers, method=metodo)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--usuario", default="docente")
    ap.add_argument("--password", default="docente123")
    ap.add_argument("--cantidad", type=int, default=80)
    ap.add_argument("--con-nota-real", type=float, default=0.6, help="Proporción con nota real registrada")
    args = ap.parse_args()

    token = pedir(f"{args.api}/api/auth/login", "POST",
                  {"username": args.usuario, "password": args.password}, form=True)["access_token"]
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "StudentPerformanceFactors.csv")
    df = df[df["Exam_Score"] <= 100].dropna().sample(args.cantidad, random_state=7)

    for i, (_, fila) in enumerate(df.iterrows(), start=1):
        datos = {v: (int(fila[v]) if isinstance(fila[v], (int, float)) else fila[v]) for v in VARIABLES}
        datos["codigo_estudiante"] = f"EST-{1000 + i}"
        r = pedir(f"{args.api}/api/predicciones", "POST", datos, token)
        if i <= int(args.cantidad * args.con_nota_real):
            pedir(f"{args.api}/api/predicciones/{r['id']}/nota-real", "PUT", {"nota_real": float(fila["Exam_Score"])}, token)
    print(f"{args.cantidad} predicciones cargadas")
