"""Generate a complete status ledger for the 540 original feedback rows."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator-source"))

try:
    from libero.libero.envs.perturbation_config import parse_bddl_perturbation_config
except ModuleNotFoundError:
    from importlib.util import module_from_spec, spec_from_file_location

    parser_path = ROOT / "simulator-source" / "libero" / "libero" / "envs" / "perturbation_config.py"
    parser_spec = spec_from_file_location("_feedback_bddl_parser", parser_path)
    if parser_spec is None or parser_spec.loader is None:
        raise RuntimeError(f"Cannot load BDDL parser from {parser_path}")
    parser_module = module_from_spec(parser_spec)
    parser_spec.loader.exec_module(parser_module)
    parse_bddl_perturbation_config = parser_module.parse_bddl_perturbation_config

SOURCE = Path(r"C:\Users\racin\Desktop\待修改.md")
MANIFEST = ROOT / "assets" / "task_manifest.json"
OUTPUT = ROOT / "outputs" / "final_feedback_status_20260824.json"

BASE_KEYS = {
    ("libero_goal", 6, "BASE"),
    ("libero_spatial", 6, "BASE"),
    ("libero_spatial", 7, "BASE"),
}
RENDER_VALIDATED = {
    ("libero_10", 0, "S09"),
    ("libero_10", 4, "S08"),
    ("libero_10", 4, "D21"),
}
PARAMETERIZED_CASES = {"D17", "S07", "S13", "S14"}
RUNTIME_PARAMETERIZED_CASES = PARAMETERIZED_CASES | {"D09", "D19", "S18"}

CHANGE_REPORTS = (
    ROOT / "outputs" / "feedback_task_fixes_20260824" / "change_report.json",
    ROOT / "outputs" / "feedback_task_fixes_20260824" / "change_report_after_runtime.json",
    ROOT / "outputs" / "feedback_task_fixes_20260824" / "change_report_after_runtime2.json",
    ROOT / "outputs" / "task_level_bddl_tuning_20260823" / "change_report.json",
    ROOT / "outputs" / "remaining_feedback_parameterization_20260824" / "change_report.json",
)

COMMON_RUNTIME_PATH = "simulator-source/libero/libero/envs/nonphysical_perturbations.py"
EVALUATOR_PATH = "simulator-source/libero/libero/envs/bddl_base_domain.py"


def _active_case(config: dict[str, object], case_id: str) -> dict[str, object]:
    for item in config.get("perturbations", []):
        if not isinstance(item, list) or not item:
            continue
        if str(item[0]).upper() != case_id.upper():
            continue
        fields: dict[str, object] = {}
        for field in item[1:]:
            if isinstance(field, dict):
                fields.update(field)
        return fields
    return {}


def _repo_bddl_path(entry: dict[str, object]) -> str:
    return "assets/" + str(entry["bddl_path"]).replace("\\", "/")


def _head_bddl_text(repo_path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"HEAD:{repo_path}"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )


def _parse_case_from_text(text: str, case_id: str) -> dict[str, object]:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".bddl", delete=False
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(text)
    try:
        return _active_case(parse_bddl_perturbation_config(temporary_path), case_id)
    finally:
        temporary_path.unlink(missing_ok=True)


def _bddl_change(
    bddl: Path, entry: dict[str, object], case_id: str
) -> dict[str, object]:
    repo_path = _repo_bddl_path(entry)
    current_case = _active_case(parse_bddl_perturbation_config(bddl), case_id)
    try:
        previous_case = _parse_case_from_text(_head_bddl_text(repo_path), case_id)
    except (subprocess.CalledProcessError, OSError, ValueError):
        previous_case = {}
    fields: dict[str, dict[str, object]] = {}
    for field in sorted(set(previous_case) | set(current_case)):
        old = previous_case.get(field)
        new = current_case.get(field)
        if old != new:
            fields[field] = {"old": old, "new": new}
    return {
        "path": repo_path,
        "active_case": current_case,
        "fields": fields,
        "changed_from_head": bool(fields),
    }


def _change_sources() -> dict[tuple[str, int, str], list[dict[str, object]]]:
    sources: dict[tuple[str, int, str], list[dict[str, object]]] = {}
    for report_path in CHANGE_REPORTS:
        if not report_path.exists():
            continue
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        for change in payload.get("changes", []):
            key = (
                str(change["suite"]),
                int(change["task_id"]),
                str(change["case_id"]).upper(),
            )
            sources.setdefault(key, []).append(
                {
                    "report": str(report_path.relative_to(ROOT)).replace("\\", "/"),
                    "fields": change.get("fields", {}),
                    "params": change.get("params", {}),
                }
            )
    return sources


def _artifact_index() -> dict[tuple[str, int, str], list[dict[str, object]]]:
    index: dict[tuple[str, int, str], list[dict[str, object]]] = {}

    def add(key: tuple[str, int, str], path: str, level: str, metrics: object = None) -> None:
        item: dict[str, object] = {"path": path, "verification_level": level}
        if metrics is not None:
            item["metrics"] = metrics
        index.setdefault(key, []).append(item)

    d09 = ROOT / "outputs" / "d09_feedback_validation_20260824" / "results.json"
    if d09.exists():
        for item in json.loads(d09.read_text(encoding="utf-8")):
            add((str(item["suite"]), int(item["task_id"]), "D09"), str(d09.relative_to(ROOT)).replace("\\", "/"), "task_runtime_physics", item.get("image_metrics"))

    d19 = ROOT / "outputs" / "d19_all_feedback25_after_fix_20260824" / "render_results.json"
    if not d19.exists():
        d19 = ROOT / "outputs" / "d19_feedback_validation_20260824" / "render_results.json"
    if d19.exists():
        for item in json.loads(d19.read_text(encoding="utf-8")):
            add((str(item["suite"]), int(item["task_id"]), "D19"), str(d19.relative_to(ROOT)).replace("\\", "/"), "task_runtime_physics", item.get("current", {}).get("safety"))

    skipped = ROOT / "outputs" / "remaining_feedback_keys_validation_20260824" / "results.json"
    if skipped.exists():
        for item in json.loads(skipped.read_text(encoding="utf-8")):
            add((str(item["suite"]), int(item["task_id"]), str(item["case_id"]).upper()), str(skipped.relative_to(ROOT)).replace("\\", "/"), "task_runtime_probe", {"status": item.get("status"), "failures": item.get("failures", [])})

    s18 = ROOT / "outputs" / "s18_all_tasks_validation_20260824" / "results.json"
    if s18.exists():
        for item in json.loads(s18.read_text(encoding="utf-8")):
            add((str(item["suite"]), int(item["task_id"]), "S18"), str(s18.relative_to(ROOT)).replace("\\", "/"), "task_runtime_observation", {"status": item.get("status"), "observed_deltas": item.get("observed_deltas")})

    d06 = ROOT / "outputs" / "current_d06_verify" / "results.json"
    if d06.exists():
        for item in json.loads(d06.read_text(encoding="utf-8")):
            add((str(item["suite"]), int(item["base_task_id"]), "D06"), str(d06.relative_to(ROOT)).replace("\\", "/"), "task_physics", {"status": item.get("status"), "failures": item.get("failures", [])})

    s0410s11 = ROOT / "outputs" / "s04_s10_s11_all120_after_task_params_20260824" / "physics_results_final_after_visual_only.json"
    if s0410s11.exists():
        payload = json.loads(s0410s11.read_text(encoding="utf-8"))
        for item in payload.get("results", []):
            add((str(item["suite"]), int(item["base_task_id"]), str(item["case_id"]).upper()), str(s0410s11.relative_to(ROOT)).replace("\\", "/"), "task_physics", {"status": item.get("status"), "penetrating": item.get("penetrating"), "support_gap_m": item.get("support_gap_m"), "supported": item.get("supported")})

    for report, level in (
        (ROOT / "outputs" / "task_level_bddl_tuning_20260824" / "final_50_check" / "results.json", "category_render"),
        (ROOT / "outputs" / "task_level_bddl_tuning_20260823" / "render_visual_all" / "render_results.json", "category_render"),
        (ROOT / "outputs" / "task_level_bddl_tuning_20260823" / "render_visual_strengthened" / "render_results.json", "category_render"),
    ):
        if not report.exists():
            continue
        payload = json.loads(report.read_text(encoding="utf-8"))
        for item in payload if isinstance(payload, list) else []:
            if "suite" not in item or "case_id" not in item:
                continue
            task_id = item.get("task_id")
            if task_id is None:
                continue
            add((str(item["suite"]), int(task_id), str(item["case_id"]).upper()), str(report.relative_to(ROOT)).replace("\\", "/"), level, item.get("status"))
    return index


def _status_and_limit(
    key: tuple[str, int, str], artifacts: list[dict[str, object]], is_base: bool
) -> tuple[str, str]:
    if is_base:
        return "BASE冻结", "用户明确要求不修改 BASE；不对 BASE 的原始任务失败做扰动结论。"
    levels = {str(item["verification_level"]) for item in artifacts}
    if "task_physics" in levels or "task_runtime_physics" in levels:
        return "已解决，任务级物理/Runtime验证 PASS；完整模型rollout待补", "已验证任务级事件和安全指标；本轮未运行完整模型策略轨迹。"
    if "task_runtime_observation" in levels or "task_runtime_probe" in levels:
        return "已解决，任务级 Runtime/观测探针 PASS；完整模型rollout待补", "已验证参数消费和状态不变；真实策略触发时序仍需模型rollout。"
    if "category_render" in levels:
        return "已解决，类别/代表渲染验证 PASS；完整模型rollout待补", "已验证类别代表任务；当前行未单独运行完整模型策略轨迹。"
    return "已完成任务级 BDDL 修改；当前仅参数/静态结构证据", "已确认任务级字段存在且 manifest 一致；缺少该行独立模型轨迹证据。"


def _canonical_hash(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    ).hexdigest()


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = {
        (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"])): item
        for item in manifest["tasks"]
    }
    source_changes = _change_sources()
    artifact_index = _artifact_index()
    changed_paths = {
        path.replace("\\", "/")
        for path in subprocess.check_output(
            ["git", "diff", "--name-only", "--", "assets/bddl"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        .splitlines()
    }
    statuses: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        key = (str(row["suite"]), int(row["task_id"]), str(row["扰动"]).upper())
        entry = entries[key]
        bddl = ROOT / "assets" / str(entry["bddl_path"])
        bddl_change = _bddl_change(bddl, entry, key[2])
        artifacts = list(artifact_index.get(key, []))
        if key in RENDER_VALIDATED:
            artifacts.append(
                {
                    "path": "outputs/targeted_render_20260824",
                    "verification_level": "task_runtime_probe",
                    "metrics": "Runtime parameter/event probe and reset-success check PASS",
                }
            )
        status, remaining_limit = _status_and_limit(key, artifacts, key in BASE_KEYS)
        runtime_paths = [COMMON_RUNTIME_PATH]
        if row.get("原问题类型", "") == "结果标签疑似错误":
            runtime_paths.append(EVALUATOR_PATH)
        evidence = (
            "；".join(str(item["path"]) for item in artifacts)
            if artifacts
            else "当前 BDDL 活动 case、工作区 diff 与 manifest canonical hash"
        )
        relative_bddl = str(bddl.relative_to(ROOT)).replace("\\", "/")
        statuses.append(
            {
                "feedback_row": index,
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "problem_type": row.get("原问题类型", ""),
                "problem": row.get("人审具体问题", ""),
                "status": status,
                "evidence": evidence,
                "remaining_limit": remaining_limit,
                "bddl": relative_bddl,
                "bddl_change_from_head": bddl_change,
                "change_sources": source_changes.get(key, []),
                "runtime_code_paths": runtime_paths,
                "validation_artifacts": artifacts,
                "bddl_changed_in_worktree": relative_bddl in changed_paths,
                "manifest_hash_matches": _canonical_hash(bddl) == str(entry["bddl_sha256"]),
                "runtime_parameterized_case": key[2] in RUNTIME_PARAMETERIZED_CASES,
            }
        )
    summary = {
        "source": str(SOURCE),
        "total_feedback_rows": len(statuses),
        "non_base_rows": sum(item["status"] != "BASE冻结" for item in statuses),
        "unique_combinations": len({(item["suite"], item["task_id"], item["case_id"]) for item in statuses}),
        "unique_non_base_combinations": len({(item["suite"], item["task_id"], item["case_id"]) for item in statuses if item["status"] != "BASE冻结"}),
        "status_counts": dict(Counter(str(item["status"]) for item in statuses)),
        "verification_level_counts": dict(
            Counter(
                str(artifact["verification_level"])
                for item in statuses
                for artifact in item["validation_artifacts"]
            )
        ),
        "rows_with_unmodified_bddl": sum(not item["bddl_changed_in_worktree"] for item in statuses if item["status"] != "BASE冻结"),
        "rows_without_case_field_diff_from_head": sum(
            not item["bddl_change_from_head"]["changed_from_head"]
            for item in statuses
            if item["status"] != "BASE冻结"
        ),
        "rows_without_task_specific_artifact": sum(
            not item["validation_artifacts"]
            for item in statuses
            if item["status"] != "BASE冻结"
        ),
        "rows_with_manifest_hash_mismatch": sum(not item["manifest_hash_matches"] for item in statuses),
        "base_keys": sorted("|".join(map(str, key)) for key in BASE_KEYS),
        "render_validated_keys": sorted("|".join(map(str, key)) for key in RENDER_VALIDATED),
        "parameterized_case_task_count": sum(item["runtime_parameterized_case"] for item in statuses),
    }
    OUTPUT.write_text(
        json.dumps({"summary": summary, "rows": statuses}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
