from app.alerts.adapters import build_alert_from_classification_event


INTERNAL_HEADERS = {"X-Internal-Api-Key": "demo-internal-key"}


def sample_detection(**overrides):
    data = {
        "detection_id": "api-det-1",
        "file_id": "file-99",
        "malware_family": "Ransomware",
        "risk_score": 91.0,
        "malware_probability": 0.95,
        "source_module": "classification",
    }
    data.update(overrides)
    return data


def ingest(client, detection=None):
    payload = build_alert_from_classification_event(
        detection or sample_detection()
    )
    return client.post(
        "/api/v1/alerts/ingest",
        json=payload.model_dump(mode="json"),
        headers=INTERNAL_HEADERS,
    )


def test_ingest_and_get_alert(client):
    resp = ingest(client)

    assert resp.status_code == 201
    body = resp.json()

    assert body["severity"] == "critical"
    assert body["status"] == "detected"
    assert body["isRead"] is False

    alert_id = body["id"]

    get_resp = client.get(f"/api/v1/alerts/{alert_id}")

    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == alert_id


def test_list_alerts_empty(client):
    resp = client.get("/api/v1/alerts")

    assert resp.status_code == 200
    assert resp.json() == []


def test_get_alert_not_found(client):
    resp = client.get(
        "/api/v1/alerts/00000000-0000-0000-0000-000000000000"
    )

    assert resp.status_code == 404


def test_ingest_requires_internal_key(client):
    payload = build_alert_from_classification_event(sample_detection())

    resp = client.post(
        "/api/v1/alerts/ingest",
        json=payload.model_dump(mode="json"),
        headers={"X-Internal-Api-Key": "wrong-key"},
    )

    assert resp.status_code == 401


def test_mark_as_read(client):
    created = ingest(client).json()

    resp = client.patch(
        f"/api/v1/alerts/{created['id']}/read"
    )

    assert resp.status_code == 200
    assert resp.json()["isRead"] is True


def test_update_status(client):
    created = ingest(client).json()

    resp = client.patch(
        f"/api/v1/alerts/{created['id']}/status",
        json={"status": "under_investigation"},
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "under_investigation"


def test_resolve_alert(client):
    created = ingest(client).json()

    resp = client.patch(
        f"/api/v1/alerts/{created['id']}/resolve"
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"
    assert resp.json()["resolvedAt"] is not None


def test_invalid_status_rejected(client):
    created = ingest(client).json()

    resp = client.patch(
        f"/api/v1/alerts/{created['id']}/status",
        json={"status": "not_a_real_status"},
    )

    assert resp.status_code == 422


def test_duplicate_detection_id_is_idempotent(client):
    detection = sample_detection(
        detection_id="duplicate-api-1"
    )

    first = ingest(client, detection).json()
    second = ingest(client, detection).json()

    assert first["id"] == second["id"]

    alerts = client.get("/api/v1/alerts").json()
    assert len(alerts) == 1
