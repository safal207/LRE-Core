# LRE-Core

[![Live Demo](https://img.shields.io/badge/🌊_Live_Demo-Try_Now-64ffda?style=for-the-badge)](https://safal207.github.io/LRE-Core/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)](https://www.python.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Enabled-green?style=flat-square)](https://github.com/safal207/LRE-Core)

> Experimental runtime integration sandbox for Liminal protocols: decision dispatch, presence semantics, identity signals, transport events, history inspection, and dashboard-visible behavior.

## Review links

- Grant evidence: [docs/GRANT_EVIDENCE.md](docs/GRANT_EVIDENCE.md)
- Event registry: [docs/EVENT_REGISTRY.md](docs/EVENT_REGISTRY.md)
- Dashboard history viewer: [docs/DASHBOARD_HISTORY_VIEWER.md](docs/DASHBOARD_HISTORY_VIEWER.md)
- Runtime decision protocol: [src/lre_dp.py](src/lre_dp.py)
- Event constants: [src/core/events.py](src/core/events.py)
- Action registry: [src/execution/registry.py](src/execution/registry.py)
- Server demo: [src/examples/server_demo.py](src/examples/server_demo.py)
- Dashboard: [tools/dashboard.html](tools/dashboard.html)

## 🚀 Quick Start

**Try the live dashboard:** [https://safal207.github.io/LRE-Core/](https://safal207.github.io/LRE-Core/)

**Then run the server locally:**

```bash
# 1. Clone and setup
git clone https://github.com/safal207/LRE-Core.git
cd LRE-Core
pip install -r requirements.txt

# 2. Start the WebSocket server
python src/examples/server_demo.py

# 3. Open the live dashboard
# Visit: https://safal207.github.io/LRE-Core/
# Dashboard will auto-connect to your local server!
```

**Alternative (Local Only):**
```bash
# Just open the local file
open tools/dashboard.html
```

## Architecture
LRE-Core serves as an experimental runtime integration environment for the Liminal ecosystem. It demonstrates interaction between key protocol surfaces:

- **LRE-DP (Liminal Runtime Environment - Decision Protocol)**: Executes registered decisions/actions based on runtime inputs.
- **DML (Decision Markup Language / DMP)**: Proposes actions and defines decision logic.
- **LPI (Liminal Presence Interface)**: Provides presence and interaction-context semantics.
- **LRI (Living Relational Identity)**: Provides relational identity and continuity signals.
- **LTP (Liminal Thread Secure Protocol)**: Transport and event-framing layer in this runtime context.

## Integration Map
The following interactions are defined in the core integration:
- `DML` <-> `LRE-DP`: DML proposes actions, LRE-DP executes them.
- `LRE-DP` <-> `LPI`: LRE-DP checks presence info via LPI.
- `DML` <-> `LPI`: DML logic may depend on presence.
- `LRI` <-> `DML`: LRI routes information relevant to DML.

## Protocols
The protocols are integrated as submodules in `src/`:

- [LTP](./src/ltp)
- [LPI](./src/lpi)
- [LRE-DP](./src/lre_dp.py)
- [DMP / DML](./src/dml)
- [LRI](./src/lri)

## Web UI Dashboard

### 🌐 Live Demo (Hybrid Mode)

**Hosted Dashboard:** [https://safal207.github.io/LRE-Core/](https://safal207.github.io/LRE-Core/)

This is a "hybrid app":
- **Frontend:** Hosted on GitHub Pages (always available)
- **Backend:** Runs locally on your machine (`ws://localhost:8000`)

**How it works:**
1. Visit the live dashboard URL
2. Run `python src/examples/server_demo.py` on your machine
3. The hosted page connects to your local server
4. You can share the URL with anyone - they just need to run the server locally

### 📁 Local Development

For development, use the local copy:

```bash
# Start server
python src/examples/server_demo.py

# Open local dashboard
open tools/dashboard.html
```

### Features
- Real-time WebSocket connection with auto-reconnect
- Live event stream with color-coded logs
- Quick action buttons (Ping, Echo, Custom, Shutdown)
- Latency tracking
- Zero dependencies (pure HTML/CSS/JS)

## Scope boundary

LRE-Core is best evaluated as a runnable integration sandbox and demonstration environment.

It is not a production multi-agent operating system, not a certified safety enforcement layer, and not the canonical source of semantics for every protocol it integrates.

Short version:

```text
LRE-Core is the lab bench.
The Liminal Evidence Stack is the formal reviewer path.
```
