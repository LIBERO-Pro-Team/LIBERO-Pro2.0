import math

import pytest
from pydantic import ValidationError

from libero_remote.protocol.models import CreateSessionRequest, StepRequest


def test_phase_one_session_request_rejects_unsupported_options() -> None:
    with pytest.raises(ValidationError):
        CreateSessionRequest(protocol_version="2.0")

    with pytest.raises(ValidationError):
        CreateSessionRequest(variant="object")


def test_session_request_validates_controller_mode() -> None:
    assert CreateSessionRequest(control_mode="absolute").control_mode == "absolute"

    with pytest.raises(ValidationError):
        CreateSessionRequest(control_mode="velocity")


@pytest.mark.parametrize("invalid_value", [math.nan, math.inf, -math.inf])
def test_step_request_rejects_non_finite_actions(invalid_value: float) -> None:
    with pytest.raises(ValidationError):
        StepRequest(
            episode_id="episode-1",
            expected_step_index=0,
            request_id="request-1",
            action=[0.0, invalid_value],
        )
