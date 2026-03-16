# Bugs & Issues

## BUG-1: SSRF — `_is_safe_url` does not block private/internal IPs

**File:** `src/learning_agent/tools/web_fetcher.py` (line 13)
**Severity:** Medium
**Status:** Resolved — `web_fetcher.py` removed; tool no longer used.

The docstring claims "Reject non-HTTP(S) schemes and bare IPs to prevent SSRF" but the function only validates the URL scheme. It does **not** reject private or internal IP addresses.

On a Vertex AI deployment, an attacker who can influence the LLM's tool calls could fetch internal endpoints such as the GCP metadata server (`http://169.254.169.254/`), loopback (`http://127.0.0.1/`), or private-network hosts (`http://10.x.x.x/`).

**Fix:** Add hostname resolution and reject RFC-1918 / link-local / loopback addresses inside `_is_safe_url`.

---

## BUG-2: Dependency version mismatch between local and deploy

**Files:** `pyproject.toml` (line 7) / `src/learning_agent/requirements.txt` (line 1)
**Severity:** Medium
**Status:** Open

- **Local** (`pyproject.toml`): pins `google-adk==1.27.1`
- **Deploy** (`requirements.txt`): uses `google-cloud-aiplatform[adk,agent_engines]` with **no version constraint**

The deployed environment may install a different ADK version than what was tested locally, causing silent behavior differences or outright failures.

**Fix:** Pin `google-cloud-aiplatform` to a specific version in `requirements.txt`, or at minimum set a compatible range that matches the local ADK version.

---

## BUG-3: Express Mode toggle is dead code

**File:** `src/learning_agent/agent_engine_app.py` (line 8)
**Severity:** Low
**Status:** Resolved

```python
if False:  # Whether or not to use Express Mode
    vertexai.init(api_key=os.environ.get("GOOGLE_API_KEY"))
```

The `if False:` literal makes the Express Mode branch unreachable. This is dead code that will never execute regardless of configuration.

**Fix:** Replace with an environment variable check:

```python
if os.environ.get("USE_EXPRESS_MODE", "").lower() == "true":
```
