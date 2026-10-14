from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windows_eval_launchers_only_override_max_steps_when_requested() -> None:
    for name in ("Start-Pi0RemoteEval.ps1", "Start-XvlaRemoteEval.ps1"):
        script = (ROOT / "scripts" / name).read_text(encoding="utf-8")

        assert "[Nullable[int]]$MaxSteps" in script
        assert '$PSBoundParameters.ContainsKey("MaxSteps")' in script
        assert '$runnerArgs += @("--max-steps", $MaxSteps)' in script
        assert "[int]$MaxSteps =" not in script


def test_windows_eval_launchers_forward_variant() -> None:
    for name in ("Start-Pi0RemoteEval.ps1", "Start-XvlaRemoteEval.ps1"):
        script = (ROOT / "scripts" / name).read_text(encoding="utf-8")

        assert '[string]$Variant = "base"' in script
        assert '"--variant", $Variant' in script
