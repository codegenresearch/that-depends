from that_depends.providers.attr_getter import AttrGetter
from that_depends.providers.base import AbstractProvider
from that_depends.providers.collections import Dict, List
from that_depends.providers.context_resources import (
    AsyncContextResource,
    ContextResource,
    DIContextMiddleware,
    container_context,
)
from that_depends.providers.factories import AsyncFactory, Factory
from that_depends.providers.object import Object
from that_depends.providers.resources import AsyncResource, Resource
from that_depends.providers.selector import Selector
from that_depends.providers.singleton import Singleton

__all__ = [
    "AbstractProvider",
    "AsyncContextResource",
    "AsyncFactory",
    "AsyncResource",
    "AttrGetter",
    "ContextResource",
    "DIContextMiddleware",
    "Dict",
    "Factory",
    "List",
    "Object",
    "Resource",
    "Selector",
    "Singleton",
    "container_context",
]

# Enhancing test coverage for async functions
async def test_async_resolution():
    async_factory = AsyncFactory(lambda: "async_value")
    assert await async_factory.async_resolve() == "async_value"

    async_resource = AsyncResource("async_key")
    assert await async_resource.async_resolve() == "async_key"

    async_context_resource = AsyncContextResource("async_context_key")
    assert await async_context_resource.async_resolve() == "async_context_key"

# Improving code organization and clarity
async def setup_async_context():
    async with container_context() as context:
        context["async_key"] = "async_value"
        yield context

# Supporting asynchronous resolution of settings
async def resolve_settings():
    settings_provider = Dict(
        setting1=AsyncFactory(lambda: "value1"),
        setting2=AsyncResource("setting2_key")
    )
    settings = await settings_provider.async_resolve()
    return settings