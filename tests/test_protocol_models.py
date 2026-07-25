import math

import pytest
from pydantic import ValidationError

from libero_remote.protocol.models import ActionSchema, CreateSessionRequest, StepRequest


def test_phase_one_session_request_rejects_unsupported_options() -> None:
    with pytest.raises(ValidationError):
        CreateSessionRequest(protocol_version="2.0")

    with pytest.raises(ValidationError):
        CreateSessionRequest(variant="object")


def test_session_request_validates_controller_mode() -> None:
    assert CreateSessionRequest(control_mode="absolute").control_mode == "absolute"

    with pytest.raises(ValidationError):
        CreateSessionRequest(control_mode="velocity")


def test_action_schema_requires_complete_control_semantics() -> None:
    common = {
        "shape": [7],
        "low": [-1.0] * 7,
        "high": [1.0] * 7,
        "controller": "OSC_POSE",
        "control_mode": "absolute",
        "control_freq": 20,
    }

    with pytest.raises(ValidationError):
        ActionSchema(**common)

    schema = ActionSchema(
        **common,
        translation_frame="world",
        rotation_frame="world",
        rotation_representation="axis_angle",
        gripper_semantics="negative_open_positive_close_zero_hold",
    )

    assert schema.rotation_representation == "axis_angle"
    assert schema.gripper_semantics == "negative_open_positive_close_zero_hold"


@pytest.mark.parametrize("invalid_value", [math.nan, math.inf, -math.inf])
def test_step_request_rejects_non_finite_actions(invalid_value: float) -> None:
    with pytest.raises(ValidationError):
        StepRequest(
            episode_id="episode-1",
            expected_step_index=0,
            request_id="request-1",
            action=[0.0, invalid_value],
        )
