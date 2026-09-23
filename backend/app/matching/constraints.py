from collections.abc import Sequence
from typing import Protocol


class ClientLike(Protocol):
    @property
    def state(self) -> str: ...

    @property
    def insurance_payer(self) -> str: ...


class ProviderLike(Protocol):
    @property
    def license_states(self) -> Sequence[str]: ...

    @property
    def insurance_panels(self) -> Sequence[str]: ...


def is_eligible(client: ClientLike, provider: ProviderLike) -> bool:
    """Static hard constraints only (state licensed, payer paneled); capacity is dynamic."""
    return (
        client.state in provider.license_states
        and client.insurance_payer in provider.insurance_panels
    )
