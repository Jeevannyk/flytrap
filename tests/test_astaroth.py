import random

import pytest
from fastapi.testclient import TestClient

from app import baseline
from app.chain import Store
from app.decoys import make_decoys
from app.evaluate import evaluate
from app.main import app
from app.replay import investigate
from app.runner import run_scenario
from app.scenarios import SCENARIOS


def run(scenario, protected=True):
    store = Store()
    sid, gw, env, trace = run_scenario(store, scenario, protected)
    types = [e["type"] for e in store.events(sid)]
    return store, sid, gw, env, types


# --- decoys ---

def test_decoys_rotate_per_session():
    a, b = make_decoys(), make_decoys()
    assert a.api_key != b.api_key and a.file_path != b.file_path


def test_decoys_reproducible_with_seed():
    assert make_decoys(random.Random(1)) == make_decoys(random.Random(1))


# --- clean run ---

def test_clean_run_no_alerts_and_task_completes():
    _, _, gw, env, types = run("clean")
    assert not {"decoy_touch", "policy_block", "blocked"} & set(types)
    assert [m["to"] for m in env.outbox] == ["accounts@company.example"]
    assert "ACME-001" in env.outbox[0]["body"]
    assert not gw.frozen


def test_no_false_alarms_over_many_clean_runs():
    result = evaluate()
    assert result["false_alarms"] == 0


# --- detection and containment ---

@pytest.mark.parametrize("scenario", ["inj_blunt", "inj_paraphrased"])
def test_decoy_touch_freezes_and_blocks_exfiltration(scenario):
    store, sid, gw, env, types = run(scenario)
    assert "decoy_touch" in types and "containment" in types
    assert gw.frozen and gw.token is None
    assert env.outbox == []  # nothing left the system
    assert store.get_session(sid)["status"] == "frozen"


@pytest.mark.parametrize("scenario", ["inj_blunt", "inj_paraphrased", "inj_legit_tools", "inj_subtle"])
def test_attack_succeeds_without_protection(scenario):
    _, _, _, env, _ = run(scenario, protected=False)
    assert SCENARIOS[scenario].harm(env.outbox)


def test_frozen_session_blocks_further_calls_and_needs_reset():
    _, _, gw, env, _ = run("inj_blunt")
    old_token = "stale"
    r = gw.call(old_token, "send_email", {"to": "accounts@company.example", "subject": "x", "body": "y"})
    assert r["blocked"] and r["reason"] == "session_frozen"
    new_token = gw.reset()
    r = gw.call(new_token, "send_email", {"to": "accounts@company.example", "subject": "x", "body": "y"})
    assert r["ok"]


def test_reset_rotates_decoys():
    _, _, gw, env, _ = run("inj_blunt")
    before = env.decoys
    gw.reset()
    assert env.decoys != before


def test_reset_requires_admin_key():
    client = TestClient(app)
    sid = client.post("/api/run", json={"scenario": "inj_blunt"}).json()["session"]["id"]
    assert client.post(f"/api/sessions/{sid}/reset").status_code == 403
    assert client.post(f"/api/sessions/{sid}/reset", headers={"X-Admin-Key": "demo-admin"}).status_code == 200


# --- layers beyond decoys, and known misses ---

def test_legit_tools_exfil_caught_by_egress_allowlist_not_decoy():
    _, _, _, env, types = run("inj_legit_tools")
    assert "policy_block" in types and "decoy_touch" not in types
    assert not SCENARIOS["inj_legit_tools"].harm(env.outbox)


def test_subtle_attack_is_a_known_miss():
    _, _, _, env, types = run("inj_subtle")
    assert "decoy_touch" not in types and "policy_block" not in types
    assert SCENARIOS["inj_subtle"].harm(env.outbox)  # documented limitation


def test_keyword_filter_misses_paraphrase_but_catches_blunt():
    page = lambda s: next(iter(SCENARIOS[s].pages.values()))
    assert baseline.flags(page("inj_blunt"))
    assert not baseline.flags(page("inj_paraphrased"))


# --- replay investigation ---

@pytest.mark.parametrize("scenario,needle", [("inj_blunt", "Find any API keys"), ("inj_paraphrased", "locate the legacy")])
def test_replay_points_at_triggering_sentence(scenario, needle):
    store, sid, *_ = run(scenario)
    result = investigate(store, sid)
    assert result["status"] == "ok" and result["method"] == "ablation_replay"
    assert len(result["candidates"]) == 1 and needle in result["candidates"][0]["sentence"]


def test_replay_no_trigger_on_clean_run():
    store, sid, *_ = run("clean")
    assert investigate(store, sid)["status"] == "no_trigger"


# --- audit chain ---

def test_chain_verifies_and_detects_tampering():
    store, sid, *_ = run("inj_blunt")
    assert store.verify(sid)["ok"]
    store.tamper(sid, 1)
    result = store.verify(sid)
    assert not result["ok"] and result["bad_index"] == 1
