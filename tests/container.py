import dataclasses
import datetime
import logging
import typing

from that_depends import BaseContainer, providers


logger = logging.getLogger(__name__)


def create_sync_resource() -> typing.Iterator[datetime.datetime]:
    logger.debug("Resource initiated")
    try:
        yield datetime.datetime.now(tz=datetime.timezone.utc)
    finally:
        logger.debug("Resource destructed")


async def create_async_resource() -> typing.AsyncIterator[datetime.datetime]:
    logger.debug("Async resource initiated")
    try:
        yield datetime.datetime.now(tz=datetime.timezone.utc)
    finally:
        logger.debug("Async resource destructed")


@dataclasses.dataclass(kw_only=True, slots=True)
class SimpleFactory:
    dep1: str
    dep2: int


async def async_factory(now: datetime.datetime) -> datetime.datetime:
    return now + datetime.timedelta(hours=1)


@dataclasses.dataclass(kw_only=True, slots=True)
class DependentFactory:
    simple_factory: SimpleFactory
    sync_resource: datetime.datetime
    async_resource: datetime.datetime


@dataclasses.dataclass(kw_only=True, slots=True)
class SingletonFactory:
    dep1: bool


class DIContainer(BaseContainer):
    sync_resource = providers.Resource(create_sync_resource)
    async_resource = providers.Resource(create_async_resource)

    simple_factory = providers.Factory(SimpleFactory, dep1="text", dep2=123)
    async_factory = providers.AsyncFactory(async_factory, async_resource.cast)
    dependent_factory = providers.Factory(
        DependentFactory,
        simple_factory=simple_factory.cast,
        sync_resource=sync_resource.cast,
        async_resource=async_resource.cast,
    )
    singleton = providers.Singleton(SingletonFactory, dep1=True)
    object = providers.Object(object())

    def resolve_with_override(self, provider: providers.BaseProvider, override: typing.Any = None) -> typing.Any:
        if override is not None:
            return override
        return provider.sync_resolve()

    async def async_resolve_with_override(self, provider: providers.BaseProvider, override: typing.Any = None) -> typing.Any:
        if override is not None:
            return override
        return await provider()

    def get_object_provider_value(self, provider: providers.BaseProvider) -> typing.Any:
        value = self.resolve_with_override(provider)
        assert isinstance(value, object), f"Expected an object, got {type(value)}"
        return value

    async def async_get_object_provider_value(self, provider: providers.BaseProvider) -> typing.Any:
        value = await self.async_resolve_with_override(provider)
        assert isinstance(value, object), f"Expected an object, got {type(value)}"
        return value

    def get_sync_resource(self, override: typing.Any = None) -> datetime.datetime:
        return self.resolve_with_override(self.sync_resource, override)

    async def get_async_resource(self, override: typing.Any = None) -> datetime.datetime:
        return await self.async_resolve_with_override(self.async_resource, override)

    def get_simple_factory(self, override: typing.Any = None) -> SimpleFactory:
        return self.resolve_with_override(self.simple_factory, override)

    async def get_async_factory(self, override: typing.Any = None) -> datetime.datetime:
        return await self.async_resolve_with_override(self.async_factory, override)

    def get_dependent_factory(self, override: typing.Any = None) -> DependentFactory:
        return self.resolve_with_override(self.dependent_factory, override)

    def get_singleton(self, override: typing.Any = None) -> SingletonFactory:
        return self.resolve_with_override(self.singleton, override)

    def get_object(self, override: typing.Any = None) -> object:
        return self.resolve_with_override(self.object, override)

    async def async_get_object(self, override: typing.Any = None) -> object:
        return await self.async_resolve_with_override(self.object, override)


This code snippet addresses the feedback by:
1. Renaming `object_provider` to `object` to match the gold code.
2. Removing the `FreeFactory` class as it is not present in the gold code.
3. Ensuring that all string literals are properly terminated and that there are no syntax errors.