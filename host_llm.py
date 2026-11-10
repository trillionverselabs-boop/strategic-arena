"""Build the host model from this machine's own Hermes configuration.

Why this exists
---------------
`ctx.llm` only exists inside the agent plugin's `register(ctx)`. In the Hermes
desktop deployment the dashboard routes and the agent plugin can end up in
different processes (the backend that serves `/api/plugins/<id>/*` and the
plugin-host that runs `register`), and no in-process trick — module global,
`sys.modules` holder, registry object — survives a process boundary. Every run
then dies with "LLM not bound in backend", which is a product failure dressed up
as a configuration error.

So the routes get their own way to the model: the same provider credentials the
host itself uses, read from `~/.hermes` on every run (never cached — the OAuth
agent key rotates). Local-first: nothing leaves the machine except the request
to the provider the user already pays for.

The agent half still binds `ctx.llm` when it can; that path is preferred because
the host owns provider routing and token refresh. This is the floor beneath it.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

TIMEOUT_S = 180
_UA = "hermes-upfront/0.4"


def _hermes_root() -> Path:
    """The root home, not the profile dir: auth.json lives at the root."""
    env = os.environ.get("HERMES_HOME")
    if env:
        p = Path(env)
        # a profile dir is <root>/profiles/<name> — auth.json is two levels up
        if p.parent.name == "profiles":
            return p.parent.parent
        return p
    return Path.home() / ".hermes"


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _config_model() -> tuple[str, str]:
    """(provider, model) from config.yaml, without a YAML dependency."""
    try:
        import yaml  # type: ignore

        cfg = yaml.safe_load((_hermes_root() / "config.yaml").read_text(encoding="utf-8")) or {}
    except Exception:
        return "", ""
    model = cfg.get("model") or {}
    if not isinstance(model, dict):
        return "", ""
    provider = str(model.get("provider") or "")
    name = str(model.get("default") or model.get("model") or "")
    return provider, name


class HostLlm:
    """`complete(messages, temperature=..., model=...)` -> object with `.text`.

    Deliberately stdlib-only: the plugin must not depend on a particular `openai`
    SDK version being present in whichever process serves the routes.
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.calls = 0

    class _Result:
        def __init__(self, text: str):
            self.text = text

    def complete(self, messages, temperature=None, model=None, **kwargs):
        body = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.6 if temperature is None else temperature,
        }
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": _UA,
            },
            method="POST",
        )
        self.calls += 1
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                payload = json.loads(resp.read().decode("utf-8", "ignore"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "ignore")[:300]
            except Exception:
                pass
            raise RuntimeError(
                f"model call failed: HTTP {exc.code} from {self.base_url} — {detail}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"model call failed: {exc}") from exc

        try:
            choice = (payload.get("choices") or [])[0]
            text = ((choice.get("message") or {}).get("content") or "").strip()
        except Exception:
            text = ""
        if not text:
            raise RuntimeError("model returned an empty answer")
        return self._Result(text)


def build_host_llm(model: str = "") -> HostLlm:
    """The active provider from local Hermes state. Raises with a plain reason."""
    provider, default_model = _config_model()
    auth = _read_json(_hermes_root() / "auth.json")
    providers = auth.get("providers") or {}
    if not provider:
        provider = str(auth.get("active_provider") or "")

    entry = providers.get(provider) or {}
    base = str(entry.get("inference_base_url") or entry.get("base_url") or "")
    key = str(entry.get("agent_key") or entry.get("access_token") or entry.get("api_key") or "")

    if not base:
        # last resort: the Nous inference API is the platform this ships on
        base = "https://inference-api.nousresearch.com/v1"
    if not key:
        raise RuntimeError(
            "no model credentials found: the agent half never bound the host model, "
            "and this machine has no stored credentials for the active provider "
            f"({provider or 'unknown'}). Run `hermes auth add {provider or 'nous'}` once."
        )

    return HostLlm(base_url=base, api_key=key, model=model or default_model or "default")


def available() -> bool:
    """True when a self-built model is possible — used for a clear health read."""
    try:
        build_host_llm()
        return True
    except Exception:
        return False
