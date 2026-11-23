import io

import pandas as pd

from .conftest import DATASET


def test_salud(client):
    r = client.get("/api/salud")
    assert r.status_code == 200
    assert r.json()["modelo_activo"] == "v1"


def test_login_incorrecto(client):
    r = client.post("/api/auth/login", data={"username": "admin", "password": "mal"})
    assert r.status_code == 401


def test_sin_token(client, estudiante):
    assert client.post("/api/predicciones", json=estudiante).status_code == 401


def test_cors(client):
    r = client.options("/api/predicciones", headers={"Origin": "http://localhost:5173",
                                                      "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_modelo_inicial_cumple_requisitos(client, docente):
    r = client.get("/api/modelo/metricas", headers=docente).json()
    assert r["modelo"]["version"] == "v1"
    assert round(r["modelo"]["mae"], 3) == 0.376      # mismo resultado que el notebook
    assert all(req["cumple"] for req in r["requisitos"])


def test_prediccion_e_historial(client, docente, estudiante):
    r = client.post("/api/predicciones", json=estudiante, headers=docente)
    assert r.status_code == 201, r.text
    p = r.json()
    assert 0 <= p["nota_estimada"] <= 100
    assert p["riesgo"] == (p["nota_estimada"] < 65)
    assert p["factores_en_contra"]

    h = client.get("/api/predicciones", params={"codigo": "EST-0001"}, headers=docente).json()
    assert h["total"] >= 1
    assert h["items"][0]["entrada"]["Attendance"] == 70

    r = client.put(f"/api/predicciones/{p['id']}/nota-real", json={"nota_real": 61}, headers=docente)
    assert r.json()["nota_real"] == 61


def test_prediccion_invalida(client, docente, estudiante):
    estudiante["Motivation_Level"] = "Altísima"
    assert client.post("/api/predicciones", json=estudiante, headers=docente).status_code == 422
    estudiante["Motivation_Level"] = "High"
    estudiante["Attendance"] = 150
    assert client.post("/api/predicciones", json=estudiante, headers=docente).status_code == 422


def test_advertencia_fuera_de_rango(client, docente, estudiante):
    estudiante["Attendance"] = 40   # válido, pero el entrenamiento solo vio 60-100
    r = client.post("/api/predicciones", json=estudiante, headers=docente).json()
    assert r["advertencias"]


def test_docente_no_reentrena(client, docente):
    assert client.post("/api/modelo/reentrenar", json={}, headers=docente).status_code == 403


def test_subir_csv_invalido(client, admin):
    csv = b"Hours_Studied,Attendance\n1,2\n"
    r = client.post("/api/datasets", files={"archivo": ("malo.csv", csv, "text/csv")}, headers=admin)
    assert r.status_code == 422


def test_subir_y_reentrenar(client, admin):
    df = pd.read_csv(DATASET).sample(frac=0.9, random_state=1)
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    r = client.post("/api/datasets", files={"archivo": ("actualizado.csv", buffer.getvalue(), "text/csv")},
                    headers=admin)
    assert r.status_code == 201, r.text
    dataset_id = r.json()["dataset"]["id"]

    # el mismo archivo no se puede subir dos veces
    r2 = client.post("/api/datasets", files={"archivo": ("actualizado.csv", buffer.getvalue(), "text/csv")},
                     headers=admin)
    assert r2.status_code == 409

    r = client.post("/api/modelo/reentrenar", json={"dataset_id": dataset_id, "incluir_notas_reales": True},
                    headers=admin)
    assert r.status_code == 202
    # TestClient ejecuta la tarea en segundo plano antes de devolver la respuesta
    e = client.get(f"/api/modelo/entrenamientos/{r.json()['id']}", headers=admin).json()
    assert e["estado"] == "completado", e
    assert e["modelo_version"] == "v2"

    versiones = client.get("/api/modelo/versiones", headers=admin).json()
    assert len(versiones) == 2
    assert sum(v["estado"] == "activo" for v in versiones) == 1


def test_activar_version_anterior(client, admin):
    v1 = [v for v in client.get("/api/modelo/versiones", headers=admin).json() if v["version"] == "v1"][0]
    r = client.post(f"/api/modelo/versiones/{v1['id']}/activar", headers=admin)
    assert r.status_code == 200
    assert client.get("/api/salud").json()["modelo_activo"] == "v1"


def test_monitoreo(client, docente, estudiante):
    for i in range(30):
        estudiante["codigo_estudiante"] = f"EST-{i:04d}"
        estudiante["Hours_Studied"] = 30 + i % 10
        client.post("/api/predicciones", json=estudiante, headers=docente)
    m = client.get("/api/modelo/monitoreo", headers=docente).json()
    assert m["suficientes_datos"]
    assert {v["variable"] for v in m["variables"]} >= {"Hours_Studied", "Attendance"}


def test_plantilla_y_contrato(client, docente):
    r = client.get("/api/datasets/plantilla", headers=docente)
    assert r.status_code == 200 and "Exam_Score" in r.text
    c = client.get("/api/modelo/contrato", headers=docente).json()
    assert len(c["campos"]) == 18
