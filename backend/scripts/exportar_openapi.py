"""Exporta la especificación OpenAPI (Swagger) a docs/api/openapi.json y openapi.yaml.

Uso (desde la carpeta backend):  python scripts/exportar_openapi.py
"""
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app  # noqa: E402

destino = Path(__file__).resolve().parents[2] / "docs" / "api"
destino.mkdir(parents=True, exist_ok=True)
spec = app.openapi()
spec["servers"] = [{"url": "http://localhost:8000", "description": "Servidor local"}]
(destino / "openapi.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
(destino / "openapi.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"OpenAPI exportado en {destino}")
