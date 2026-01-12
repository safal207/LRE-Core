# LRE-Core
Liminal multi-agent runtime with smart decision governance, presence semantics, and high-load emergency handling.

## Architecture
LRE-Core serves as the foundational runtime integration environment for the Liminal ecosystem. It orchestrates interaction between key protocols:

- **LRE-DP (Liminal Runtime Environment - Decision Protocol)**: Executes decisions based on inputs via LPI + LRI.
- **DML (Decision Markup Language / DMP)**: Proposes actions and defines decision logic.
- **LPI (Liminal Presence Interface)**: Manages presence semantics.
- **LRI (Living Relational Identity)**: Handles routing updates.
- **LTP (Liminal Thread Secure Protocol)**: Transport layer.

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
