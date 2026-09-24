import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

NOT_IMPLEMENTED = "matching engine v1 not implemented yet"


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_rank_candidates_drops_ineligible_providers() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_rank_candidates_drops_providers_with_no_spare_capacity() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_rank_candidates_sorts_best_score_first() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_rank_candidates_breaks_ties_by_spare_capacity() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_rank_candidates_works_on_generated_and_database_rows() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_provider_loads_count_only_capacity_holding_matches() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_provider_loads_are_scoped_to_one_strategy() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_candidates_endpoint_ranks_eligible_providers_in_the_clients_run() -> None: ...


@pytest.mark.skip(reason=NOT_IMPLEMENTED)
def test_candidates_endpoint_reflects_capacity_used_by_existing_matches() -> None: ...


def test_candidates_endpoint_unknown_client_returns_404() -> None:
    res = client.get(f"/api/v1/clients/{uuid.uuid4()}/candidates")
    assert res.status_code == 404


def test_candidates_endpoint_rejects_out_of_range_limit() -> None:
    assert client.get(f"/api/v1/clients/{uuid.uuid4()}/candidates?limit=0").status_code == 422
    assert client.get(f"/api/v1/clients/{uuid.uuid4()}/candidates?limit=51").status_code == 422
