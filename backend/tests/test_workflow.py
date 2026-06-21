import os

os.environ["DATABASE_URL"] = "sqlite:///./test_vigil.db"

from fastapi.testclient import TestClient

from app.entrypoint import app


def operator(client: TestClient):
    response = client.post("/auth/session", json={"username": "operator", "password": "vigil-demo"})
    assert response.status_code == 200


def payload(email: str, consent: bool = True):
    return {
        "name": "Marina Costa", "email": email, "company": "Acme Finance", "job_title": "CISO",
        "company_size": "1000+", "challenge": "Precisamos priorizar vulnerabilidades e manter conformidade LGPD.",
        "consent_email": consent,
    }


def test_lead_can_reach_booked_meeting():
    with TestClient(app) as client:
        lead = client.post("/leads", json=payload("marina.costa@example.com")).json()
        assert lead["status"] == "confirmation_pending"
        operator(client)
        assert client.post(f"/leads/{lead['id']}/reply", json={"content": "Confirmo minha presenca"}).json()["status"] == "confirmed"
        assert client.post(f"/leads/{lead['id']}/attendance", json={"attended": True, "demo_interest": True}).json()["status"] == "meeting_offered"
        slot = client.get("/slots").json()[0]
        assert client.post("/meetings", json={"lead_id": lead["id"], "slot_id": slot["id"]}).status_code == 201


def test_opt_out_blocks_future_actions():
    with TestClient(app) as client:
        lead = client.post("/leads", json=payload("rafael.lima@example.com")).json()
        operator(client)
        assert client.post(f"/leads/{lead['id']}/reply", json={"content": "Por favor, remova meu contato"}).json()["status"] == "opted_out"
        assert client.post(f"/leads/{lead['id']}/attendance", json={"attended": True, "demo_interest": True}).status_code == 409


def test_no_consent_never_starts_processing():
    with TestClient(app) as client:
        lead = client.post("/leads", json=payload("sem.consentimento@example.com", consent=False)).json()
        assert lead["status"] == "consent_required"
        operator(client)
        assert client.post(f"/leads/{lead['id']}/reply", json={"content": "Confirmo"}).status_code == 409


def test_viewer_masks_pii():
    with TestClient(app) as client:
        client.post("/leads", json=payload("viewer@example.com"))
        assert client.post("/auth/session", json={"username": "viewer", "password": "viewer-demo"}).status_code == 200
        result = client.get("/dashboard").json()
        assert "***" in result["leads"][0]["email"]
