"""Die Fassungsabfrage: /api/health meldet version.json, damit offene Oberflächen eine neue Fassung bemerken."""
from __future__ import annotations

import json

from app import config


def test_health_meldet_fassung_aus_version_json(client):
    erwartet = json.loads(config._VERSIONSDATEI.read_text(encoding="utf-8"))["version"]
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": erwartet}
    assert config.VERSION == erwartet
