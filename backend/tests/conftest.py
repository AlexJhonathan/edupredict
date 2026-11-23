import os
import shutil
import tempfile
from pathlib import Path

import pytest

# base de datos y modelos de prueba en una carpeta temporal
_TMP = tempfile.mkdtemp(prefix="edupredict_test_")
os.environ["STORAGE_DIR"] = _TMP
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

DATASET = Path(__file__).resolve().parent.parent / "data" / "StudentPerformanceFactors.csv"


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    shutil.rmtree(_TMP, ignore_errors=True)


def _token(client, usuario, password):
    r = client.post("/api/auth/login", data={"username": usuario, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client):
    return _token(client, "admin", "admin123")


@pytest.fixture(scope="session")
def docente(client):
    return _token(client, "docente", "docente123")


@pytest.fixture
def estudiante():
    return {"codigo_estudiante": "EST-0001", "Hours_Studied": 12, "Attendance": 70, "Parental_Involvement": "Low",
            "Access_to_Resources": "Medium", "Extracurricular_Activities": "No", "Sleep_Hours": 7,
            "Previous_Scores": 65, "Motivation_Level": "Low", "Internet_Access": "Yes", "Tutoring_Sessions": 0,
            "Family_Income": "Low", "Teacher_Quality": "Medium", "School_Type": "Public",
            "Peer_Influence": "Negative", "Physical_Activity": 3, "Learning_Disabilities": "No",
            "Parental_Education_Level": "High School", "Distance_from_Home": "Far"}
