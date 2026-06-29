"""Wire-surface schemas are self-describing — every api.schemas field is documented.

Agents construct and read the API straight from the OpenAPI schema, so a field's
description is the only documentation that crosses the wire. This gate holds every
public ``glyde.api.schemas`` model field to a non-empty description.

Scope is deliberately the api surface only: core models document via class
docstrings and are projected into these schemas before serialization. A ``type``
discriminator field (if any) is exempt — its ``Literal`` value is its own
documentation.
"""

import importlib
import inspect
import pkgutil

from pydantic import BaseModel

import glyde.api.schemas

_DISCRIMINATOR = "type"


def _schema_models() -> set[type[BaseModel]]:
    """Return every public, field-bearing pydantic model defined in glyde.api.schemas."""
    models: set[type[BaseModel]] = set()
    for info in pkgutil.walk_packages(
        glyde.api.schemas.__path__, prefix=f"{glyde.api.schemas.__name__}."
    ):
        module = importlib.import_module(info.name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseModel)
                and obj.__module__.startswith(glyde.api.schemas.__name__)
                and obj.model_fields
            ):
                models.add(obj)
    return models


def test_api_schema_fields_have_descriptions() -> None:
    """Every public api.schemas model field (bar the discriminator) carries a description."""
    missing = [
        f"{model.__module__.removeprefix('glyde.api.schemas.')}.{model.__qualname__}.{name}"
        for model in _schema_models()
        for name, field in model.model_fields.items()
        if name != _DISCRIMINATOR and not (field.description or "").strip()
    ]
    assert not missing, "api.schemas fields missing a description:\n" + "\n".join(sorted(missing))
