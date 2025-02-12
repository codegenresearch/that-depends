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
class FreeFactory:
    dependent_factory: DependentFactory
    sync_resource: str


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

    _overrides: typing.Dict[str, typing.Any] = {}

    @classmethod
    def override_provider(cls, provider_name: str, override: typing.Any):
        cls._overrides[provider_name] = override

    @classmethod
    async def get_provider(cls, provider_name: str, default: typing.Any = None):
        if provider_name in cls._overrides:
            provider = cls._overrides[provider_name]
            if hasattr(provider, 'cast'):
                return provider.cast()
            return provider
        return await getattr(cls, provider_name)()

    @classmethod
    async def sync_resource_override(cls) -> datetime.datetime:
        return await cls.get_provider('sync_resource')

    @classmethod
    async def async_resource_override(cls) -> datetime.datetime:
        return await cls.get_provider('async_resource')

    @classmethod
    async def simple_factory_override(cls) -> SimpleFactory:
        return await cls.get_provider('simple_factory')

    @classmethod
    async def async_factory_override(cls) -> datetime.datetime:
        return await cls.get_provider('async_factory')

    @classmethod
    async def dependent_factory_override(cls) -> DependentFactory:
        return await cls.get_provider('dependent_factory')

    @classmethod
    async def singleton_override(cls) -> SingletonFactory:
        return await cls.get_provider('singleton')

    @classmethod
    async def object_provider(cls, provider_name: str, default: typing.Any = None):
        provider = await cls.get_provider(provider_name, default)
        assert provider, f"Provider {provider_name} should not be None"
        return provider

    @classmethod
    async def resolve(cls, factory_class: typing.Type):
        provider_name = factory_class.__name__.lower()
        return await cls.object_provider(provider_name)

    @classmethod
    async def resolver(cls, factory_class: typing.Type):
        return cls.resolve(factory_class)