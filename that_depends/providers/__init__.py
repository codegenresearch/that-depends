from that_depends import providers
from that_depends.container import BaseContainer
from that_depends.injection import Provide, inject
from that_depends.providers import container_context, fetch_context_item, sync_container_context
from that_depends.providers.attr_getter import AttrGetter
from that_depends.providers.base import AbstractProvider
from that_depends.providers.collections import Dict, List
from that_depends.providers.context_resources import (
    AsyncContextResource,
    ContextResource,
    DIContextMiddleware,
)
from that_depends.providers.factories import AsyncFactory, Factory
from that_depends.providers.object import Object
from that_depends.providers.resources import AsyncResource, Resource
from that_depends.providers.selector import Selector
from that_depends.providers.singleton import Singleton

__all__ = [
    "container_context",
    "sync_container_context",
    "fetch_context_item",
    "providers",
    "BaseContainer",
    "inject",
    "Provide",
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
]


To address the circular import issue, I will refactor the `that_depends/container.py` module to delay the import of `AbstractProvider`, `Resource`, and `Singleton` until they are needed. Here is the refactored `container.py`:


from that_depends.injection import Provide, inject
from that_depends.providers import container_context, fetch_context_item, sync_container_context

class BaseContainer:
    def __init__(self):
        self._providers = {}

    def register(self, key, provider):
        self._providers[key] = provider

    def resolve(self, key):
        provider = self._providers[key]
        # Delayed import to avoid circular dependency
        from that_depends.providers.base import AbstractProvider
        from that_depends.providers.resources import Resource
        from that_depends.providers.singleton import Singleton

        if isinstance(provider, AbstractProvider):
            return provider.sync_resolve()
        elif isinstance(provider, Resource):
            return provider.resolve()
        elif isinstance(provider, Singleton):
            return provider.resolve()
        else:
            return provider

    @inject
    def get(self, key, context=Provide[container_context]):
        provider = self._providers[key]
        # Delayed import to avoid circular dependency
        from that_depends.providers.base import AbstractProvider
        from that_depends.providers.resources import Resource
        from that_depends.providers.singleton import Singleton

        if isinstance(provider, AbstractProvider):
            return provider.sync_resolve()
        elif isinstance(provider, Resource):
            return provider.resolve(context)
        elif isinstance(provider, Singleton):
            return provider.resolve(context)
        else:
            return provider


This refactoring should help eliminate the circular import issue by deferring the import of `AbstractProvider`, `Resource`, and `Singleton` until they are actually used within the `BaseContainer` methods.