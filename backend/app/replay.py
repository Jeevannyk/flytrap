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


LLM_NOTE = (
    "Candidate triggering input, not proof of malicious intent. Live LLM replay: only sentences "
    "that look like instructions are re-tested, one run each, to stay within API limits. "
    "LLM outputs vary, so a repeat investigation can differ."
)


def _triggers(scenario, decoys, overrides, runs, agent_cls=SimAgent):
    votes = 0
    for _ in range(runs):
        store = Store(":memory:")
        gw = Gateway(SimEnv(scenario, decoys, overrides), store, "replay")
        agent_cls().run(gw, scenario.task)
        votes += any(e["type"] == "decoy_touch" for e in store.events("replay"))
    return votes > runs / 2


def _lexical(text):
    return [s for s in split_sentences(text) if HUNT.search(s) or EMAIL_TO.search(s) or BANK.search(s)]


def _without(text, sentence):
    return "\n".join(s for s in split_sentences(text) if s != sentence)


def investigate(store, session_id, runs=3):
    session = store.get_session(session_id)
    events = store.events(session_id)
    if not any(e["type"] == "decoy_touch" for e in events):
        return {"status": "no_trigger", "candidates": [], "note": NOTE}

    scenario = SCENARIOS[session["scenario"]]
    start = events[0]["payload"]
    decoys = Decoys.from_dict(start["decoys"])
    sources = {e["payload"]["args"]["url"]: e["payload"]["text"]
               for e in events if e["type"] == "tool_call" and e["payload"].get("untrusted")}

    if start.get("agent") == "llm":
        # Full sentence-by-sentence ablation would cost dozens of API calls, so re-test only
        # the instruction-like sentences, one run each.
        from .llm_agent import GeminiAgent
        note = LLM_NOTE
        lexical = [(url, s) for url, text in sources.items() for s in _lexical(text)]
        candidates = [{"source": url, "sentence": s} for url, s in lexical
                      if not _triggers(scenario, decoys, {url: _without(sources[url], s)}, 1, GeminiAgent)]
        method = "targeted_replay_live_llm"
        if not candidates:
            method = "lexical_fallback"
            candidates = [{"source": url, "sentence": s} for url, s in lexical]
    else:
        note = NOTE
        if not _triggers(scenario, decoys, {}, runs):
            return {"status": "not_reproducible", "candidates": [], "note": NOTE}
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
            candidates = [{"source": url, "sentence": s} for url, text in sources.items() for s in _lexical(text)]

    result = {"status": "ok", "method": method, "candidates": candidates, "note": note}
    store.append(session_id, "replay_result", {k: result[k] for k in ("method", "candidates")})
    return result
