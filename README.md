# LRE-Core
Liminal multi-agent runtime with smart decision governance, presence semantics, and high-load emergency handling.

## Architecture

LRE-Core serves as the foundational runtime integration environment for the Liminal ecosystem. It orchestrates interaction between key protocols:

- **LRE-DP (Liminal Runtime Environment - Decision Protocol)**: Executes decisions based on inputs.
- **DML (Decision Markup Language)**: Proposes actions and defines decision logic.
- **LPI (Liminal Presence Interface)**: Manages presence semantics.
- **LRI (Liminal Routing Interface)**: Handles routing updates.
- **LTP (Liminal Transport Protocol)**: Transport layer (placeholder).

## Integration Map

The following interactions are defined in the core integration:

- `DML` <-> `LRE-DP`: DML proposes actions, LRE-DP executes them.
- `LRE-DP` <-> `LPI`: LRE-DP checks presence info via LPI.
- `DML` <-> `LPI`: DML logic may depend on presence.
- `LRI` <-> `DML`: LRI routes information relevant to DML.

## Protocols

Currently, the protocols are integrated as internal skeleton modules in `src/`.

- [LRE-DP](./src/lre_dp.py)
- [DML](./src/dml.py)
- [LPI](./src/lpi.py)
- [LRI](./src/lri.py)
- [LTP](./src/ltp.py)

## License

MIT License
