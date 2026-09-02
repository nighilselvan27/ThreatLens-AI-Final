def test_ingest_and_get_alert(client):
    payload = {
        "detection_id": "api-det-1",
        "file_id": "file-99",
        "malware_family": "Ransomware",
        "risk_score": 91.0,
        "confidence_score": 0.88,
        "source_module": "classification",
    }
    resp = client.post("/alerts/ingest", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["severity"] == "critical"
    assert body["status"] == "new"

    alert_id = body["id"]
    get_resp = client.get(f"/alerts/{alert_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["detection_id"] == "api-det-1"


def test_list_alerts_empty_input(client):
    resp = client.get("/alerts/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_alert_not_found(client):
    resp = client.get("/alerts/nonexistent-id")
    assert resp.status_code == 404


def test_ingest_missing_required_field(client):
    resp = client.post("/alerts/ingest", json={"file_id": "x"})
    assert resp.status_code == 422  # missing detection_id / risk_score


def test_update_status_flow(client):
    payload = {"detection_id": "api-det-2", "risk_score": 15.0}
    create_resp = client.post("/alerts/ingest", json=payload)
    alert_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/alerts/{alert_id}/status", json={"status": "acknowledged"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "acknowledged"


def test_update_status_not_found(client):
    resp = client.patch("/alerts/missing-id/status", json={"status": "resolved"})
    assert resp.status_code == 404


def test_duplicate_ingest_is_idempotent_via_api(client):
    payload = {"detection_id": "dup-api-1", "risk_score": 50.0}
    r1 = client.post("/alerts/ingest", json=payload)
    r2 = client.post("/alerts/ingest", json=payload)
    assert r1.json()["id"] == r2.json()["id"]

    all_alerts = client.get("/alerts/").json()
    ids = [a["id"] for a in all_alerts if a["detection_id"] == "dup-api-1"]
    assert len(ids) == 1
