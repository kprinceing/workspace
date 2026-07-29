#!/usr/bin/env python3
"""Generate synthetic night-session teaching data.

Replicates the DGP in week2/code/sim_workflow.do (seed 20260721).
Outputs CSV files used by workshop/night exercises.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260721
N_STATES = 50
YEARS = list(range(2000, 2020))
OUT_DIR = Path(__file__).resolve().parent / "data"


def true_effect(event_time: int | None) -> float:
    if event_time is None:
        return 0.0
    if event_time < 0:
        return 0.0
    if event_time == 0:
        return -0.25
    if event_time == 1:
        return -0.50
    if event_time == 2:
        return -0.75
    return -1.00


def build_panel(rng: np.random.Generator) -> list[dict]:
    state_fe = rng.normal(0, 1.8, N_STATES)
    state_slope = rng.normal(0, 0.025, N_STATES)
    rows: list[dict] = []

    for state in range(1, N_STATES + 1):
        treated = state <= 35
        if treated:
            adopt_year = 2006 + (state - 1) // 4
            adopt_year = min(adopt_year, 2014)
        else:
            adopt_year = None

        for year in YEARS:
            event_time = year - adopt_year if treated and adopt_year is not None else None
            effect = true_effect(event_time)
            common_trend = 0.08 * (year - 2000)
            y0 = (
                55
                + state_fe[state - 1]
                + state_slope[state - 1] * (year - 2000)
                + common_trend
                + rng.normal(0, 0.55)
            )
            teen_emp = y0 + effect
            teen_emp_s1 = teen_emp + (0.11 * (year - 2000) if treated else 0.0)
            post = int(treated and adopt_year is not None and year >= adopt_year)

            rows.append(
                {
                    "state": state,
                    "year": year,
                    "treated": int(treated),
                    "adopt_year": adopt_year if adopt_year is not None else "",
                    "event_time": event_time if event_time is not None else "",
                    "teen_employment_rate": round(teen_emp, 4),
                    "teen_employment_rate_s1": round(teen_emp_s1, 4),
                    "true_effect_pp": effect,
                    "post_adoption": post,
                }
            )

    return rows


def apply_s2_loss(rows: list[dict], rng: np.random.Generator) -> list[dict]:
    """Selective merge loss among treated, low-employment rows (matches sim_workflow.do)."""
    kept: list[dict] = []
    for row in rows:
        keep = True
        if row["treated"] == 1 and row["teen_employment_rate"] < 55:
            if rng.random() < 0.28:
                keep = False
        if keep:
            kept.append(row)
    return kept


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})


def row_ledger(rows: list[dict]) -> list[dict]:
    adopting = [r for r in rows if r["treated"] == 1]
    never = [r for r in rows if r["treated"] == 0]
    return [
        {"group": "adopting", "n_state_years": len(adopting)},
        {"group": "never_treated", "n_state_years": len(never)},
        {"group": "total", "n_state_years": len(rows)},
    ]


def employment_and_weights(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Raw employment file + population weights with deliberate post-2010 code mismatch."""
    employment: list[dict] = []
    weights: list[dict] = []

    for row in rows:
        state = row["state"]
        year = row["year"]
        employment.append(
            {
                "state_id": f"ST{state:02d}",
                "year": year,
                "teen_employment_count": int(round(row["teen_employment_rate"] * 1000)),
            }
        )
        # Adopting states after 2010 use a different code in the weights file.
        if row["treated"] == 1 and year >= 2010:
            weight_state = f"ST{state:02d}X"
        else:
            weight_state = f"ST{state:02d}"
        weights.append(
            {
                "state_code": weight_state,
                "year": year,
                "population_weight": round(0.85 + (state % 7) * 0.02, 3),
            }
        )

    return employment, weights


def policy_ledger(rows: list[dict]) -> list[dict]:
    seen: set[int] = set()
    ledger: list[dict] = []
    for row in rows:
        state = row["state"]
        if state in seen:
            continue
        seen.add(state)
        ledger.append(
            {
                "state": state,
                "treated": row["treated"],
                "adopt_year": row["adopt_year"],
            }
        )
    return ledger


def answer_key() -> list[dict]:
    return [
        {"event_time": k, "true_effect_pp": true_effect(k)}
        for k in range(-4, 6)
        if k != -1
    ]


def main() -> None:
    rng = np.random.default_rng(SEED)
    panel = build_panel(rng)
    panel_s2 = apply_s2_loss(panel, rng)
    employment, weights = employment_and_weights(panel)
    ledger_s0 = row_ledger(panel)
    ledger_s2 = row_ledger(panel_s2)

    write_csv(
        OUT_DIR / "panel_s0.csv",
        panel,
        [
            "state",
            "year",
            "treated",
            "adopt_year",
            "event_time",
            "teen_employment_rate",
            "true_effect_pp",
            "post_adoption",
        ],
    )
    write_csv(
        OUT_DIR / "panel_s1.csv",
        [
            {**r, "teen_employment_rate": r["teen_employment_rate_s1"]}
            for r in panel
        ],
        [
            "state",
            "year",
            "treated",
            "adopt_year",
            "event_time",
            "teen_employment_rate",
            "true_effect_pp",
            "post_adoption",
        ],
    )
    write_csv(
        OUT_DIR / "panel_s2.csv",
        panel_s2,
        [
            "state",
            "year",
            "treated",
            "adopt_year",
            "event_time",
            "teen_employment_rate",
            "true_effect_pp",
            "post_adoption",
        ],
    )
    write_csv(
        OUT_DIR / "employment_raw.csv",
        employment,
        ["state_id", "year", "teen_employment_count"],
    )
    write_csv(
        OUT_DIR / "population_weights.csv",
        weights,
        ["state_code", "year", "population_weight"],
    )
    write_csv(
        OUT_DIR / "policy_ledger.csv",
        policy_ledger(panel),
        ["state", "treated", "adopt_year"],
    )
    write_csv(
        OUT_DIR / "answer_key_effects.csv",
        answer_key(),
        ["event_time", "true_effect_pp"],
    )
    write_csv(
        OUT_DIR / "row_ledger_s0.csv",
        ledger_s0,
        ["group", "n_state_years"],
    )
    write_csv(
        OUT_DIR / "row_ledger_s2.csv",
        ledger_s2,
        ["group", "n_state_years"],
    )

    adopting_s0 = next(r["n_state_years"] for r in ledger_s0 if r["group"] == "adopting")
    adopting_s2 = next(r["n_state_years"] for r in ledger_s2 if r["group"] == "adopting")
    never = next(r["n_state_years"] for r in ledger_s0 if r["group"] == "never_treated")

    print(f"panel_s0: {len(panel)} rows (adopting={adopting_s0}, never={never})")
    print(f"panel_s2: {len(panel_s2)} rows (adopting={adopting_s2}, never={never})")
    print(f"Wrote CSV files to {OUT_DIR}")


if __name__ == "__main__":
    main()
