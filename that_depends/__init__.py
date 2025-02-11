from that_depends import providers
from that_depends.container import BaseContainer
from that_depends.injection import Provide, inject
from that_depends.providers.context_resources import fetch_context_item
from contextlib import asynccontextmanager

__all__ = [
    "fetch_context_item",
    "providers",
    "BaseContainer",
    "inject",
    "Provide",
]

@asynccontextmanager
async def container_context():
    # Assuming the original container_context was a context manager, this is a simplified version
    try:
        # Setup code here
        yield
    finally:
        # Teardown code here
        pass