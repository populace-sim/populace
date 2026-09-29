"""Put a Python agent behind an HTTP server, to try the HTTP path locally.

    .venv/bin/python examples/http_agent_server.py --port 8765

Then point a run at it: agents={"northline": HttpAgent("http://127.0.0.1:8765/")}.
The server receives {"message": {...}} and answers {"text", "end", "actions"},
where actions are the same verbs as AgentContext: resolve, credit, dispatch,
promise, note. Write it in any language.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from populace.agents.basic import HelpdeskAgent  # noqa: E402
from populace.agents.http import serve  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(HelpdeskAgent("Northline Internet"), args.port)
    print(f"Agent listening on http://127.0.0.1:{args.port}/ (Ctrl-C to stop)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
