# Optimus Agent Monitor — local prototype

**Status:** experimental / not deployed. This prototype provides a read-only terminal event view and a local-only mobile-ready web UI. It is **not** a complete agent graph, production dashboard, or Codex integration.

## Prerequisites

Python 3.10+ on WSL Ubuntu. No external Python dependencies.

## Run

From repository root:

```bash
python3 -m unittest discover -s agent_monitor/tests -v
python3 agent_monitor/monitor.py watch
```

In another terminal, for local browser preview only:

```bash
python3 agent_monitor/monitor.py web --port 8765
```

Open `http://127.0.0.1:8765` **on the same machine**. The service binds only to `127.0.0.1`. It is **not accessible from a phone** and must not be exposed using port forwarding, tunnels or a public reverse proxy at this stage.

## Hook wiring — opt-in only

Review Claude Code's installed version and current hook settings before modifying them. The following is a **sample** hook entry; merge it into your existing configuration instead of overwriting existing hooks. Replace `/ABSOLUTE/REPO/PATH` with the actual WSL path.

```json
{
  "hooks": {
    "SubagentStart": [{"hooks": [{"type": "command", "command": "python3 /ABSOLUTE/REPO/PATH/agent_monitor/monitor.py ingest"}]}],
    "SubagentStop": [{"hooks": [{"type": "command", "command": "python3 /ABSOLUTE/REPO/PATH/agent_monitor/monitor.py ingest"}]}]
  }
}
```

Check hook schema against the installed Claude Code release before enabling. Hooks execute local commands and require trust review. Existing security hooks must remain unchanged.

## Security and data minimization

The collector stores only an allowlisted event name, timestamp, truncated session/agent identifier and tool name. It deliberately does **not** persist prompts, responses, tool inputs, tool outputs or environment variables. Stored identifiers may still be sensitive; the SQLite file is private to the local user and should not be committed.

Monitoring is best effort; missing events do not prove an agent is idle. An ingestion error does not block agent execution.

## Mobile-ready, not mobile-accessible

The responsive HTML is included and can be tested locally. A future phone release requires a separately approved architecture: authentication, TLS, least-privilege authorization, private network/VPN, rate limiting, audit logging, explicit retention policy, and security tests. **No production or remote access is enabled.**

## Codex

Codex event collection is **not implemented**. Build and validate a separate supported adapter rather than assuming Claude hooks apply to Codex.

## Next iteration

Add workflow graph, derived agent states, session reconciliation, and a supported Codex adapter; then test actual hooks in WSL. Do not label these features implemented until tested.
