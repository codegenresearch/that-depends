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
# Example test function for AsyncContextResource
# import asyncio
# import unittest
# from unittest.mock import AsyncMock
#
# class TestAsyncContextResource(unittest.IsolatedAsyncioTestCase):
#     async def test_async_resolve(self):
#         mock_provider = AsyncMock()
#         mock_provider.async_resolve.return_value = "test_value"
#         resource = AsyncContextResource(mock_provider)
#         result = await resource.async_resolve()
#         self.assertEqual(result, "test_value")

# Improving code organization and clarity
# Grouping related imports together
# from that_depends.providers.attr_getter import AttrGetter
# from that_depends.providers.base import AbstractProvider
# from that_depends.providers.collections import Dict, List
# from that_depends.providers.context_resources import (
#     AsyncContextResource,
#     ContextResource,
#     DIContextMiddleware,
#     container_context,
# )
# from that_depends.providers.factories import AsyncFactory, Factory
# from that_depends.providers.object import Object
# from that_depends.providers.resources import AsyncResource, Resource
# from that_depends.providers.selector import Selector
# from that_depends.providers.singleton import Singleton