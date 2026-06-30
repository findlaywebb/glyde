"""Concrete implementations of ``glyde.core`` ports.

This layer owns everything that touches the outside world: the SQLite (WAL)
store — the source of truth — and any external clients.

Public surfaces:
- ``glyde.adapters.sqlite`` — ``SqliteDigestStore``: the durable ``DigestStore``
  implementation, plus ``connect`` (the one connect path) and ``apply_migrations``
  (the forward-only migration runner).

What it does NOT do: no domain logic (that lives in ``glyde.core``), no HTTP
routing (that lives in ``glyde.api``). May import ``glyde.core`` only.

Invariants:
- Every public adapter class subclasses a port from ``glyde.core.ports``.
- Synchronous and deterministic by contract: no clock reads, no id minting, no
  ``async def`` (enforced by the purity architecture test).
"""
