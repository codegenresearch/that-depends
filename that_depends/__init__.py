import contextlib

from that_depends import providers
from that_depends.container import BaseContainer
from that_depends.injection import Provide, inject
from that_depends.providers import (
    AbstractProvider,
    AsyncContextResource,
    AsyncFactory,
    AsyncResource,
    AttrGetter,
    ContextResource,
    DIContextMiddleware,
    Dict,
    Factory,
    List,
    Object,
    Resource,
    Selector,
    Singleton,
    container_context,
    fetch_context_item,
    sync_container_context,
)

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
    "sync_container_context",
    "fetch_context_item",
    "providers",
    "BaseContainer",
    "inject",
    "Provide",
]