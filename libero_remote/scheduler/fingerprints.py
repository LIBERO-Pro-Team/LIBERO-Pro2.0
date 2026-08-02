"""Stable identities for immutable jobs and actual reset observations."""

import hashlib
from typing import Any, Dict

from libero_remote.protocol.codec import pack_message
from libero_remote.reproducibility import canonical_fingerprint


def initial_environment_reproducibility(session: Dict[str, Any]) -> Dict[str, Any]:
    environment = session.get("environment_reproducibility")
    if not isinstance(environment, dict):
        raise ValueError("Environment did not provide reproducibility metadata")
    plan = environment.get("perturbation_plan")
    state_fingerprint = environment.get("initial_state_fingerprint")
    plan_fingerprint = environment.get("perturbation_plan_fingerprint")
    if not isinstance(plan, dict) or not isinstance(state_fingerprint, str):
        raise ValueError("Environment reproducibility metadata is incomplete")
    if plan_fingerprint != canonical_fingerprint(plan):
        raise ValueError("Environment perturbation plan fingerprint is invalid")
    observation_fingerprint = hashlib.sha256(
        pack_message({"observation": session["observation"]})
    ).hexdigest()
    return {
        "initial_state_fingerprint": state_fingerprint,
        "initial_observation_fingerprint": observation_fingerprint,
        "perturbation_plan_fingerprint": plan_fingerprint,
        "perturbation_plan": plan,
    }
