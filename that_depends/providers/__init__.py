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
# Example test function for async resolution
# import asyncio
# import unittest
# from unittest.mock import AsyncMock

# class TestAsyncResolution(unittest.IsolatedAsyncioTestCase):
#     async def test_async_context_resource(self):
#         resource = AsyncContextResource(AsyncMock(return_value="test"))
#         result = await resource.async_resolve()
#         self.assertEqual(result, "test")

#     async def test_async_factory(self):
#         factory = AsyncFactory(AsyncMock(return_value="test"))
#         result = await factory.async_resolve()
#         self.assertEqual(result, "test")

#     async def test_async_resource(self):
#         resource = AsyncResource(AsyncMock(return_value="test"))
#         result = await resource.async_resolve()
#         self.assertEqual(result, "test")

# if __name__ == "__main__":
#     unittest.main()