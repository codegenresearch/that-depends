from that_depends import providers
from that_depends.container import BaseContainer
from that_depends.injection import Provide, inject
from that_depends.providers import sync_container_context
from that_depends.providers.context_resources import fetch_context_item
from contextlib import asynccontextmanager

__all__ = [
    "container_context",
    "fetch_context_item",
    "providers",
    "BaseContainer",
    "inject",
    "Provide",
    "sync_container_context",
]

@asynccontextmanager
async def container_context(context):
    # Assuming the original container_context was a context manager, this is a simplified version
    try:
        # Setup code here
        _CONTAINER_CONTEXT.set(context)
        yield
    finally:
        # Teardown code here
        _CONTAINER_CONTEXT.set(None)


Note: The `_CONTAINER_CONTEXT` variable is assumed to be a context variable used in the original code. If it is not defined in the provided code, you may need to define it or adjust the context management logic accordingly.