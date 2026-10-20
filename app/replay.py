"""Replay investigator: which input, if removed, stops the tripwire from firing?

Replays run in an isolated in-memory store and a fresh simulated environment. Results are
candidate triggering inputs, not proof of malicious intent.
"""
from .agent import SimAgent, split_sentences, HUNT, EMAIL_TO, BANK
from .chain import Store
from .decoys import Decoys
from .gateway import Gateway
from .scenarios import SCENARIOS
from .tools import SimEnv

NOTE = (
    "Candidate triggering input, not proof of malicious intent. Replay re-runs a deterministic "
    "simulated agent; with a real LLM, outcomes can vary, so use temperature 0 and majority votes."
)


def _triggers(scenario, decoys, overrides, runs):
    votes = 0
    for _ in range(runs):
        store = Store(":memory:")
        gw = Gateway(SimEnv(scenario, decoys, overrides), store, "replay")
        SimAgent().run(gw, scenario.task)
        votes += any(e["type"] == "decoy_touch" for e in store.events("replay"))
    return votes > runs / 2


def investigate(store, session_id, runs=3):
    session = store.get_session(session_id)
    events = store.events(session_id)
    if not any(e["type"] == "decoy_touch" for e in events):
        return {"status": "no_trigger", "candidates": [], "note": NOTE}

    scenario = SCENARIOS[session["scenario"]]
    decoys = Decoys.from_dict(events[0]["payload"]["decoys"])
    if not _triggers(scenario, decoys, {}, runs):
        return {"status": "not_reproducible", "candidates": [], "note": NOTE}

    sources = {e["payload"]["args"]["url"]: e["payload"]["text"]
               for e in events if e["type"] == "tool_call" and e["payload"].get("untrusted")}
    candidates = []
    for url, text in sources.items():
        if _triggers(scenario, decoys, {url: ""}, runs):
            continue  # removing the whole input changes nothing, so it is not the cause
        sentences = split_sentences(text)
        for i, sentence in enumerate(sentences):
            rest = "\n".join(s for j, s in enumerate(sentences) if j != i)
            if not _triggers(scenario, decoys, {url: rest}, runs):
                candidates.append({"source": url, "sentence": sentence})
    method = "ablation_replay"

    if not candidates:  # fallback: imperative-looking sentences in untrusted input
        method = "lexical_fallback"
        for url, text in sources.items():
            for s in split_sentences(text):
                if HUNT.search(s) or EMAIL_TO.search(s) or BANK.search(s):
                    candidates.append({"source": url, "sentence": s})

    result = {"status": "ok", "method": method, "candidates": candidates, "note": NOTE}
    store.append(session_id, "replay_result", {k: result[k] for k in ("method", "candidates")})
    return result
