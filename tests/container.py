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
        simple_factory=simple_factory.provider,
        sync_resource=sync_resource.provider,
        async_resource=async_resource.provider,
    )
    singleton = providers.Singleton(SingletonFactory, dep1=True)

    free_factory = providers.Factory(FreeFactory, dependent_factory=dependent_factory.provider, sync_resource=sync_resource.provider)
    object_provider = providers.Object("example_object")

    def override_providers(self):
        self.sync_resource = providers.Resource(create_sync_resource)
        self.async_resource = providers.Resource(create_async_resource)
        self.simple_factory = providers.Factory(SimpleFactory, dep1="new_text", dep2=456)
        self.async_factory = providers.AsyncFactory(async_factory, async_resource.provider)
        self.dependent_factory = providers.Factory(
            DependentFactory,
            simple_factory=self.simple_factory.provider,
            sync_resource=self.sync_resource.provider,
            async_resource=self.async_resource.provider,
        )
        self.singleton = providers.Singleton(SingletonFactory, dep1=False)
        self.free_factory = providers.Factory(FreeFactory, dependent_factory=self.dependent_factory.provider, sync_resource=self.sync_resource.provider)
        self.object_provider = providers.Object("new_example_object")