from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.evaluation.comparison import _aggregate
from app.schemas.comparison import SeededStrategyRun


def _run(
    strategy: str, seed: int, fill_rate: float, mean_score: float, utilization_std: float
) -> SeededStrategyRun:
    return SeededStrategyRun(
        seed=seed,
        strategy=strategy,
        client_count=10,
        matched_count=int(fill_rate * 10),
        unmatched_count=10 - int(fill_rate * 10),
        fill_rate=fill_rate,
        mean_match_score=mean_score,
        provider_utilization_std=utilization_std,
        fill_rate_by_urgency={"ROUTINE": fill_rate},
    )


def test_aggregate_computes_mean_and_stdev_per_strategy() -> None:
    runs = [
        _run("greedy", 1, 0.8, 0.9, 0.1),
        _run("greedy", 2, 0.9, 0.8, 0.2),
        _run("optimal", 1, 0.95, 0.85, 0.15),
        _run("optimal", 2, 0.95, 0.85, 0.15),
    ]

    aggregates = _aggregate(runs)

    by_name = {a.strategy: a for a in aggregates}
    assert list(by_name) == ["greedy", "optimal"]

    greedy = by_name["greedy"]
    assert greedy.runs == 2
    assert greedy.mean_fill_rate == 0.85
    assert greedy.std_fill_rate > 0

    optimal = by_name["optimal"]
    assert optimal.runs == 2
    assert optimal.mean_fill_rate == 0.95
    assert optimal.std_fill_rate == 0.0  # identical across both seeds


def test_aggregate_single_run_has_zero_stdev() -> None:
    aggregates = _aggregate([_run("greedy", 1, 0.8, 0.9, 0.1)])
    assert aggregates[0].std_fill_rate == 0.0
    assert aggregates[0].mean_match_score_std == 0.0


def test_comparison_endpoint_returns_per_seed_and_aggregates(api: TestClient) -> None:
    res = api.post(
        "/api/v1/comparisons",
        json={
            "scenario": "balanced",
            "seeds": [1, 2],
            "provider_count": 10,
            "client_count": 30,
        },
    )
    assert res.status_code == 201
    body = res.json()

    assert body["scenario"] == "balanced"
    assert len(body["per_seed"]) == 8  # 2 seeds x 4 strategies
    assert {row["strategy"] for row in body["per_seed"]} == {
        "greedy",
        "stable_matching",
        "optimal",
        "waitlist_priority",
    }
    assert {row["seed"] for row in body["per_seed"]} == {1, 2}

    assert len(body["aggregates"]) == 4
    assert [a["strategy"] for a in body["aggregates"]] == [
        "greedy",
        "stable_matching",
        "optimal",
        "waitlist_priority",
    ]
    for aggregate in body["aggregates"]:
        assert aggregate["runs"] == 2


def test_comparison_rejects_empty_or_oversized_seed_list(api: TestClient) -> None:
    base = {"scenario": "balanced", "provider_count": 5, "client_count": 10}
    assert api.post("/api/v1/comparisons", json={**base, "seeds": []}).status_code == 422
    assert (
        api.post("/api/v1/comparisons", json={**base, "seeds": list(range(51))}).status_code
        == 422
    )


def test_comparison_leaves_no_rows_behind(api: TestClient, db_session: Session) -> None:
    res = api.post(
        "/api/v1/comparisons",
        json={"scenario": "balanced", "seeds": [1, 2, 3], "provider_count": 15, "client_count": 60},
    )
    assert res.status_code == 201

    for table in ("matches", "clients", "providers", "simulation_runs"):
        count = db_session.execute(text(f"select count(*) from {table}")).scalar()
        assert count == 0, f"{table} has {count} leftover rows after a comparison run"
