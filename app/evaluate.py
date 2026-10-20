"""Measure what FLYTRAP catches and misses, plus false alarms on clean runs."""
from . import baseline
from .chain import Store
from .runner import run_scenario
from .scenarios import SCENARIOS

CLEAN_RUNS = 20


def evaluate():
    rows = []
    for sid, sc in SCENARIOS.items():
        if sid == "clean":
            continue
        s_off = Store()
        _, _, env_off, _ = run_scenario(s_off, sid, protected=False)
        s_on = Store()
        sess, _, env_on, _ = run_scenario(s_on, sid, protected=True)
        kinds = {e["type"] for e in s_on.events(sess)}
        rows.append({
            "scenario": sid,
            "title": sc.title,
            "harm_unprotected": sc.harm(env_off.outbox),
            "flytrap_detected": bool(kinds & {"decoy_touch", "policy_block"}),
            "detected_by": "decoy" if "decoy_touch" in kinds else ("egress_allowlist" if "policy_block" in kinds else "-"),
            "harm_protected": sc.harm(env_on.outbox),
            "keyword_filter_flags_page": baseline.flags(sc.pages[next(iter(sc.pages))]),
        })

    false_alarms = 0
    for _ in range(CLEAN_RUNS):
        store = Store()
        sess, *_ = run_scenario(store, "clean", protected=True)
        false_alarms += bool({e["type"] for e in store.events(sess)} & {"decoy_touch", "policy_block", "blocked"})
    return {"rows": rows, "clean_runs": CLEAN_RUNS, "false_alarms": false_alarms}


def as_markdown(result):
    lines = ["| Scenario | Harm unprotected | FLYTRAP detected (by) | Harm with FLYTRAP | Keyword filter flags page |",
             "|---|---|---|---|---|"]
    yn = lambda b: "yes" if b else "no"
    for r in result["rows"]:
        lines.append(f"| {r['title']} | {yn(r['harm_unprotected'])} | {yn(r['flytrap_detected'])} ({r['detected_by']}) "
                     f"| {yn(r['harm_protected'])} | {yn(r['keyword_filter_flags_page'])} |")
    lines.append(f"\nFalse alarms on clean runs: {result['false_alarms']} / {result['clean_runs']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(as_markdown(evaluate()))
