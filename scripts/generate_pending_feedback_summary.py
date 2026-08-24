"""Generate a category/task-level report for the 540 pending feedback rows."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = Path(r"C:\Users\racin\Desktop\待修改.md")
AUDIT = ROOT / "outputs" / "pending_task_fix_audit.json"
CHANGE_REPORT = (
    ROOT / "outputs" / "task_level_bddl_tuning_20260823" / "change_report.json"
)
OUTPUT = ROOT / "outputs" / "pending_feedback_category_summary_20260823.md"


def _load_rows() -> list[dict[str, str]]:
    with REVIEW.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _key(row: dict[str, str]) -> tuple[str, int, str]:
    return str(row["suite"]), int(row["task_id"]), str(row["扰动"]).upper()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _compact_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _main() -> None:
    rows = _load_rows()
    audit_rows = json.loads(AUDIT.read_text(encoding="utf-8"))
    audit_by_key = {
        (str(item["suite"]), int(item["task_id"]), str(item["case_id"]).upper()): item
        for item in audit_rows
    }
    change_payload = json.loads(CHANGE_REPORT.read_text(encoding="utf-8"))
    changed_by_key = {
        (str(item["suite"]), int(item["task_id"]), str(item["case_id"]).upper()): item
        for item in change_payload["changes"]
    }
    applied_by_key = {
        (str(item["suite"]), int(item["task_id"]), str(item["case_id"]).upper()): item
        for item in change_payload.get("applied_changes", [])
    }

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["扰动"]).upper()].append(row)

    lines = [
        "# LIBERO-Pro2.0 540条待修改反馈：按扰动类别与任务明细",
        "",
        f"生成时间：2026-08-23；反馈总数：{len(rows)}；扰动类别：{len(grouped)}。",
        "当前参数来自每个任务实际加载的 BDDL；`旧值→新值` 来自任务级调强账本。",
        "`公共 runtime` 表示该反馈不能仅靠 BDDL 完成，本阶段未修改公共默认值。",
        "",
        "## 总体分类",
        "",
    ]
    problem_types = Counter(str(row.get("原问题类型", "")) for row in rows)
    for name, count in problem_types.most_common():
        lines.append(f"- {name or '未分类'}：{count} 条")
    lines.extend(
        [
            "",
            f"- 当前逐条审计：{sum(bool(item.get('bddl_only_possible')) for item in audit_rows)} 条可仅 BDDL 表达，",
            f"  {sum(not bool(item.get('bddl_only_possible')) for item in audit_rows)} 条需要 runtime/资产/日志/评估器等支持。",
            f"- 任务级调强账本：218 个 BDDL-only 任务，15 个因共享代码或安全语义冻结；本阶段新增正式写回 2 个 D19 任务。",
            "",
            "## 类别与任务反馈",
            "",
        ]
    )

    for case_id in sorted(grouped, key=lambda value: (value == "BASE", value)):
        case_rows = grouped[case_id]
        lines.append(f"### {case_id}（{len(case_rows)} 条）")
        lines.append("")
        type_counts = Counter(str(row.get("原问题类型", "")) for row in case_rows)
        lines.append("反馈类型：" + "；".join(f"{name or '未分类'} {count}" for name, count in type_counts.most_common()))
        lines.append("")
        for row in sorted(case_rows, key=lambda item: (str(item["suite"]), int(item["task_id"]))):
            key = _key(row)
            audit = audit_by_key.get(key, {})
            changed = changed_by_key.get(key)
            applied = applied_by_key.get(key)
            task_label = f"{row['suite']}/task{row['task_id']}"
            lines.append(f"- **{task_label}**")
            lines.append(f"  - 反馈：{_compact_text(row.get('人审具体问题', '')) or '无文字反馈'}")
            lines.append(f"  - 原始判定：{_compact_text(row.get('原始判定', '')) or '未记录'}；问题类型：{_compact_text(row.get('原问题类型', '')) or '未分类'}")
            params = audit.get("params", {})
            lines.append(f"  - 当前 BDDL 参数：`{_json(params)}`")
            if changed:
                lines.append(f"  - 调强字段旧值→新值：`{_json(changed.get('fields', {}))}`")
            elif applied:
                lines.append(f"  - 本次实际写回：`{_json(applied.get('fields', {}))}`")
            else:
                lines.append("  - 本阶段任务级调强：未写回（需共享代码、无安全候选或该类别未纳入 BDDL-only 调强范围）")
            unsupported = audit.get("runtime_unsupported_fields", [])
            if unsupported:
                lines.append(f"  - 需要公共/专用支持的字段：`{_json(unsupported)}`")
        lines.append("")

    lines.extend(
        [
            "## 本阶段 D19 物理验证",
            "",
            "- 正式验证目录：`outputs/task_level_bddl_tuning_20260823/render_d19_final_all`。",
            "- 结果：17 个任务中 16 个 PASS；`libero_goal/task2/D19` FAIL，唯一原因是错放落稳后仍满足原任务成功条件。",
            "- 已写回 `libero_10/task9/D19`：`[0.055,0.035], 0.012 → [0.120,0.000], -0.050`；杯子渲染帧中移至微波炉右侧门旁，无穿透。",
            "- 已写回 `libero_object/task7/D19`：`[0.035,0.020], 0.005 → [0.120,0.000], -0.040`；牛奶盒渲染帧中明显移离篮筐，无其他物体联动。",
            "- 两个新增任务均满足：无目标穿透、支撑间隙 <=0.01 m、速度 <=0.25 m/s、接收器距离 <=0.18 m、非目标物额外位移 <=0.01 m、在工作区、落稳后不直接成功。",
            "",
            "## 约束与未解决项",
            "",
            "- 未修改 `simulator-source/libero/libero/envs/nonphysical_perturbations.py` 的公共逻辑、评估器、日志或触发器；该文件已有历史工作区修改，未作为本阶段新增变更处理。",
            "- `libero_goal/task2/D19` 若要同时保持安全错放和任务失败语义，需要任务级接收器/成功判定语义或共享 runtime 支持，当前保持冻结。",
            "- 视觉证据目录：`outputs/task_level_bddl_tuning_20260823/render_visual_all` 和 `outputs/task_level_bddl_tuning_20260823/render_d19_final_all`。",
        ]
    )
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "categories": len(grouped), "output": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    _main()
