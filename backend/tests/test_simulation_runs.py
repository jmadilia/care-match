from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FAKE_ID = "00000000-0000-0000-0000-000000000000"


def _create_run() -> str:
    payload = {"name": "Test Run", "seed": 42, "provider_count": 10, "client_count": 50}
    res = client.post("/api/v1/simulation-runs", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def test_simulation_run_create_get_list() -> None:
    payload = {"name": "Baseline", "seed": 7, "provider_count": 20, "client_count": 100}

    create_res = client.post("/api/v1/simulation-runs", json=payload)
    assert create_res.status_code == 201
    run = create_res.json()
    run_id = run["id"]
    assert run["seed"] == 7
    assert run["provider_count"] == 20
    assert run["client_count"] == 100

    get_res = client.get(f"/api/v1/simulation-runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Baseline"

    list_res = client.get("/api/v1/simulation-runs")
    assert list_res.status_code == 200
    assert any(r["id"] == run_id for r in list_res.json())

    missing_res = client.get(f"/api/v1/simulation-runs/{FAKE_ID}")
    assert missing_res.status_code == 404


def test_simulation_run_scenario_defaults_and_validates() -> None:
    base = {"name": "Scenario Run", "seed": 1, "provider_count": 5, "client_count": 5}

    default_res = client.post("/api/v1/simulation-runs", json=base)
    assert default_res.status_code == 201
    assert default_res.json()["scenario"] == "balanced"

    explicit_res = client.post(
        "/api/v1/simulation-runs", json={**base, "scenario": "undersupplied_state"}
    )
    assert explicit_res.status_code == 201
    assert explicit_res.json()["scenario"] == "undersupplied_state"

    bad_res = client.post("/api/v1/simulation-runs", json={**base, "scenario": "nonsense"})
    assert bad_res.status_code == 422


def test_client_arrival_day_is_stored_and_validated() -> None:
    payload = {
        "name": "Arrival Client",
        "state": "CA",
        "insurance_payer": "Aetna",
        "needed_specialties": ["anxiety"],
        "preferred_modality": "video",
        "preferred_language": "en",
        "arrival_day": 12,
    }
    res = client.post("/api/v1/clients", json=payload)
    assert res.status_code == 201
    assert res.json()["arrival_day"] == 12

    assert client.post("/api/v1/clients", json={**payload, "arrival_day": -1}).status_code == 422


def _create_small_run(scenario: str = "balanced") -> str:
    payload = {
        "name": "Generate Run",
        "scenario": scenario,
        "seed": 5,
        "provider_count": 3,
        "client_count": 8,
    }
    res = client.post("/api/v1/simulation-runs", json=payload)
    assert res.status_code == 201
    return res.json()["id"]


def _delete_population(run_id: str) -> None:
    for kind in ("clients", "providers"):
        rows = client.get(f"/api/v1/{kind}", params={"simulation_run_id": run_id}).json()
        for row in rows:
            client.delete(f"/api/v1/{kind}/{row['id']}")


def test_generate_creates_population_and_returns_summary() -> None:
    run_id = _create_small_run()
    try:
        res = client.post(f"/api/v1/simulation-runs/{run_id}/generate")
        assert res.status_code == 201
        summary = res.json()
        assert summary["provider_count"] == 3
        assert summary["client_count"] == 8
        assert summary["total_weekly_capacity"] == 8

        clients = client.get("/api/v1/clients", params={"simulation_run_id": run_id}).json()
        providers = client.get("/api/v1/providers", params={"simulation_run_id": run_id}).json()
        assert len(clients) == 8
        assert len(providers) == 3
        assert all(c["arrival_day"] is not None for c in clients)
        assert all(c["simulation_run_id"] == run_id for c in clients)
    finally:
        _delete_population(run_id)


def test_generate_twice_returns_409() -> None:
    run_id = _create_small_run()
    try:
        assert client.post(f"/api/v1/simulation-runs/{run_id}/generate").status_code == 201
        assert client.post(f"/api/v1/simulation-runs/{run_id}/generate").status_code == 409
    finally:
        _delete_population(run_id)


def test_generate_is_reproducible_across_runs_with_the_same_seed() -> None:
    first_id, second_id = _create_small_run(), _create_small_run()
    try:
        first = client.post(f"/api/v1/simulation-runs/{first_id}/generate").json()
        second = client.post(f"/api/v1/simulation-runs/{second_id}/generate").json()
        assert first == second
    finally:
        _delete_population(first_id)
        _delete_population(second_id)


def test_generate_unknown_run_returns_404() -> None:
    res = client.post(f"/api/v1/simulation-runs/{FAKE_ID}/generate")
    assert res.status_code == 404


def test_simulation_run_rejects_non_positive_counts() -> None:
    payload = {"name": "Bad", "seed": 1, "provider_count": 0, "client_count": 10}
    assert client.post("/api/v1/simulation-runs", json=payload).status_code == 422

    payload = {"name": "Bad", "seed": 1, "provider_count": 10, "client_count": -5}
    assert client.post("/api/v1/simulation-runs", json=payload).status_code == 422


def test_clients_and_providers_link_to_run_and_filter() -> None:
    run_id = _create_run()

    client_res = client.post(
        "/api/v1/clients",
        json={
            "name": "Run Client",
            "state": "CA",
            "insurance_payer": "Aetna",
            "needed_specialties": ["anxiety"],
            "preferred_modality": "video",
            "preferred_language": "en",
            "simulation_run_id": run_id,
        },
    )
    assert client_res.status_code == 201
    assert client_res.json()["simulation_run_id"] == run_id

    provider_res = client.post(
        "/api/v1/providers",
        json={
            "name": "Run Provider",
            "license_states": ["CA"],
            "specialties": ["anxiety"],
            "modalities": ["video"],
            "languages": ["en"],
            "insurance_panels": ["Aetna"],
            "weekly_capacity": 10,
            "simulation_run_id": run_id,
        },
    )
    assert provider_res.status_code == 201
    assert provider_res.json()["simulation_run_id"] == run_id

    clients = client.get("/api/v1/clients", params={"simulation_run_id": run_id}).json()
    assert len(clients) == 1
    assert clients[0]["id"] == client_res.json()["id"]

    providers = client.get("/api/v1/providers", params={"simulation_run_id": run_id}).json()
    assert len(providers) == 1
    assert providers[0]["id"] == provider_res.json()["id"]


def test_client_and_provider_reject_unknown_run() -> None:
    client_res = client.post(
        "/api/v1/clients",
        json={
            "name": "Orphan Client",
            "state": "CA",
            "insurance_payer": "Aetna",
            "needed_specialties": ["anxiety"],
            "preferred_modality": "video",
            "preferred_language": "en",
            "simulation_run_id": FAKE_ID,
        },
    )
    assert client_res.status_code == 404

    provider_res = client.post(
        "/api/v1/providers",
        json={
            "name": "Orphan Provider",
            "license_states": ["CA"],
            "specialties": ["anxiety"],
            "modalities": ["video"],
            "languages": ["en"],
            "insurance_panels": ["Aetna"],
            "weekly_capacity": 10,
            "simulation_run_id": FAKE_ID,
        },
    )
    assert provider_res.status_code == 404
