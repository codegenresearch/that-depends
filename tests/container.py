import dataclasses
import datetime
import logging
import typing
from unittest.mock import MagicMock

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

    mock_sync_resource = providers.Resource(lambda: MagicMock())
    mock_async_resource = providers.Resource(lambda: MagicMock())
    mock_simple_factory = providers.Factory(SimpleFactory, dep1="mock", dep2=0)
    mock_async_factory = providers.AsyncFactory(lambda x: MagicMock(), mock_async_resource.cast)
    mock_dependent_factory = providers.Factory(
        DependentFactory,
        simple_factory=mock_simple_factory.cast,
        sync_resource=mock_sync_resource.cast,
        async_resource=mock_async_resource.cast,
    )
    mock_singleton = providers.Singleton(SingletonFactory, dep1=False)

    def sync_resolve(self, provider, override=None):
        if override:
            return override()
        try:
            return provider.sync_resolve()
        except RuntimeError as e:
            logger.warning(f"Sync resolve failed: {e}")
            return None

    def async_resolve(self, provider, override=None):
        if override:
            return override()
        try:
            return provider.resolve()
        except RuntimeError as e:
            logger.warning(f"Async resolve failed: {e}")
            return None