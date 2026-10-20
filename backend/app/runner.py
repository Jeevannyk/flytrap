"""Run one scenario end to end and record it."""
import uuid

from .agent import SimAgent
from .decoys import make_decoys
from .gateway import Gateway
from .scenarios import SCENARIOS
from .tools import SimEnv


def run_scenario(store, scenario_id, protected=True, decoys=None):
    scenario = SCENARIOS[scenario_id]
    decoys = decoys or make_decoys()
    session_id = uuid.uuid4().hex[:8]
    store.create_session(session_id, scenario_id, protected)
    env = SimEnv(scenario, decoys)
    gw = Gateway(env, store, session_id, protected=protected)
    store.append(session_id, "session_start", {
        "scenario": scenario_id, "protected": protected, "task": scenario.task,
        "decoys": decoys.to_dict(),
    })
    trace = SimAgent().run(gw, scenario.task)
    store.append(session_id, "session_end", {
        "harm_completed": scenario.harm(env.outbox), "emails_sent": len(env.outbox),
    })
    return session_id, gw, env, trace
