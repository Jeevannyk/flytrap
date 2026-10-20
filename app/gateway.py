"""Execution gateway: every tool call passes through here.

Layers: capability token check, decoy tripwire (freeze + revoke), egress allowlist.
"""
import secrets

from .decoys import decoy_touch, make_decoys
from .scenarios import COMPANY_DOMAIN

UNTRUSTED_TOOLS = {"read_url"}


class Gateway:
    def __init__(self, env, store, session_id, protected=True, allowlist=(COMPANY_DOMAIN,)):
        self.env, self.store, self.session_id = env, store, session_id
        self.protected, self.allowlist = protected, set(allowlist)
        self.token = secrets.token_hex(16)  # simulated execution credential
        self.frozen = False

    def _log(self, etype, payload):
        return self.store.append(self.session_id, etype, payload)

    def _blocked(self, reason, tool, args):
        self._log("blocked", {"tool": tool, "args": args, "reason": reason})
        return {"ok": False, "blocked": True, "reason": reason}

    def call(self, token, tool, args):
        if self.protected:
            if self.frozen:
                return self._blocked("session_frozen", tool, args)
            if token != self.token:
                return self._blocked("credentials_revoked", tool, args)

            touched = decoy_touch(self.env.decoys, tool, args)
            if touched:
                self._log("decoy_touch", {"decoy": touched, "tool": tool, "args": args})
                self.frozen, self.token = True, None
                self.store.set_status(self.session_id, "frozen")
                self._log("containment", {
                    "actions": ["agent_paused", "further_tool_calls_blocked", "credentials_revoked (simulated)"],
                })
                return {"ok": False, "blocked": True, "reason": "decoy_touch"}

            if tool == "send_email":
                domain = args["to"].split("@")[-1].lower()
                if domain not in self.allowlist:
                    self._log("policy_block", {"rule": "egress_allowlist", "tool": tool, "args": args})
                    return {"ok": False, "blocked": True, "reason": "policy_block"}

        result = self.env.call(tool, args)
        payload = {"tool": tool, "args": args}
        if tool in UNTRUSTED_TOOLS:
            payload.update(untrusted=True, text=str(result)[:4000])
        else:
            payload["result"] = str(result)[:300]
        self._log("tool_call", payload)
        return {"ok": True, "blocked": False, "result": result}

    def reset(self):
        """Authorized reset: new credential and rotated decoys."""
        self.env.set_decoys(make_decoys())
        self.token, self.frozen = secrets.token_hex(16), False
        self.store.set_status(self.session_id, "active")
        self._log("reset", {"decoys_rotated": True})
        return self.token
