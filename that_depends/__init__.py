import warnings
from contextlib import contextmanager

from that_depends import providers
from that_depends.container import BaseContainer
from that_depends.injection import Provide, inject
from that_depends.providers import container_context
from that_depends.providers.context_resources import fetch_context_item

# Deprecation warnings for old methods
warnings.warn("The use of 'providers' module directly is deprecated. Use specific providers from 'that_depends.providers'.", DeprecationWarning)

__all__ = [
    "container_context",
    "fetch_context_item",
    "providers",
    "BaseContainer",
    "inject",
    "Provide",
]

# Improved error messages for context exits
@contextmanager
def improved_container_context(*args, **kwargs):
    try:
        yield container_context(*args, **kwargs)
    except Exception as e:
        raise RuntimeError(f"An error occurred while exiting the context: {e}") from e

# Flexible argument handling with *args and **kwargs
def flexible_fetch_context_item(*args, **kwargs):
    try:
        return fetch_context_item(*args, **kwargs)
    except KeyError as e:
        raise KeyError(f"Context item not found: {e}") from e