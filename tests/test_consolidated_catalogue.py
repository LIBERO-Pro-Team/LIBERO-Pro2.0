"""Keep the published catalogue and held-out planning compatible after branch merges."""

import json
from collections import Counter
from pathlib import Path

from libero_remote.benchmark import build_benchmark_plan
from libero_remote.benchmark_split import BenchmarkSplit
from libero_remote.environment.task_manifest import TaskManifest

ROOT = Path(__file__).resolve().parents[1]


def test_split_metadata_describes_all_published_cases() -> None:
    manifest = TaskManifest.load(str(ROOT / "assets" / "task_manifest.json"))
    payload = json.loads((ROOT / "assets" / "benchmark_split_v1.json").read_text())
    expanded = {}
    for kind, ranges in payload["case_groups"].items():
        cases = set()
        for item in ranges:
            if "-" not in item:
                cases.add(item)
            else:
                first, last = item.split("-")
                cases.update(f"{first[0]}{i:02d}" for i in range(int(first[1:]), int(last[1:]) + 1))
        expanded[kind] = cases
    assert expanded == {
        kind: {entry["case_id"] for entry in manifest.entries if entry["case_kind"] == kind}
        for kind in ("base", "static", "dynamic")
    }


def test_held_out_planning_retains_all_cases_and_published_step_limits() -> None:
    manifest = TaskManifest.load(str(ROOT / "assets" / "task_manifest.json"))
    split = BenchmarkSplit.load(ROOT / "assets" / "benchmark_split_v1.json")
    catalogue = manifest.catalog()
    train = split.filter_catalog(catalogue, "train")
    test = split.filter_catalog(catalogue, "test")
    def key(row):
        return row["suite"], row["task_id"], row["case_id"]

    train_keys, test_keys = ({key(row) for row in part["tasks"]} for part in (train, test))
    assert not train_keys & test_keys
    assert train_keys | test_keys == {key(row) for row in catalogue["tasks"]}
    assert (len(train_keys), len(test_keys)) == (1349, 339)
    assert Counter(row["case_kind"] for row in test["tasks"]) == {
        "base": 8, "static": 172, "dynamic": 159,
    }
    plan = build_benchmark_plan(test, group="all", seeds=[142, 143], init_state_ids=[0, 1])
    assert plan.rollout_count == 678
    limits = {"libero_spatial": 220, "libero_object": 280, "libero_goal": 300, "libero_10": 520}
    assert all(episode["max_steps"] == limits[episode["suite"]] for episode in plan.episodes)
    assert plan.selection["benchmark_split"]["name"] == "test"
    variants = {episode["variant"] for episode in plan.episodes}
    assert {"S22", "D20", "D21"} <= variants
    assert "D19" not in variants
