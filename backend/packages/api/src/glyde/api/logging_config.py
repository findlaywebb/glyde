"""Logging setup — the one place logging is configured for the serving process.

Key callables:
- ``setup_logging`` — configure the root logger once, idempotently. Called from
  the app lifespan at startup and by the CLI before it does work. Every module
  obtains its logger with ``logging.getLogger(__name__)`` and never configures
  handlers of its own.

What this module does NOT do:
- No ``print`` (banned across ``backend/packages`` by ruff ``T20`` and an
  architecture test) — structured logging only.
- No business logic and no per-module configuration.

Invariants:
- Idempotent: calling ``setup_logging`` more than once does not stack handlers
  (FastAPI reload, repeated CLI invocations, tests).
- The level is read from the injected ``Settings``-style argument, not the
  environment directly (config is injected; ``os.environ`` is banned here too).
"""

from __future__ import annotations

import logging

_CONFIGURED = False
_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging(level: int | str = logging.INFO) -> None:
    """Configure the root logger once with a single stream handler.

    Args:
        level: The root log level (an ``int`` or a level name). Pass a value
            derived from injected settings; never read the environment here.
    """
    global _CONFIGURED  # noqa: PLW0603 - module-singleton guard for idempotent setup
    if _CONFIGURED:
        logging.getLogger().setLevel(level)
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMAT))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    _CONFIGURED = True
