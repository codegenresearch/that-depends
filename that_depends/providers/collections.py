import typing
from operator import attrgetter

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)


class List(AbstractProvider[list[T_co]]):
    __slots__ = ("_providers", "_override")

    def __init__(self, *providers: AbstractProvider[T_co], override: list[T_co] = None) -> None:
        super().__init__()
        self._providers: typing.Final = providers
        self._override: typing.Final = override

    async def async_resolve(self) -> list[T_co]:
        if self._override:
            return self._override
        resolve_async = attrgetter('async_resolve')
        return [await resolve_async(provider)() for provider in self._providers]

    def sync_resolve(self) -> list[T_co]:
        if self._override:
            return self._override
        resolve_sync = attrgetter('sync_resolve')
        return [resolve_sync(provider)() for provider in self._providers]

    async def __call__(self) -> list[T_co]:
        return await self.async_resolve()


class Dict(AbstractProvider[dict[str, T_co]]):
    __slots__ = ("_providers", "_override")

    def __init__(self, **providers: AbstractProvider[T_co]) -> None:
        super().__init__()
        self._providers: typing.Final = providers
        self._override: typing.Final = None

    async def async_resolve(self) -> dict[str, T_co]:
        if self._override:
            return self._override
        resolve_async = attrgetter('async_resolve')
        return {key: await resolve_async(provider)() for key, provider in self._providers.items()}

    def sync_resolve(self) -> dict[str, T_co]:
        if self._override:
            return self._override
        resolve_sync = attrgetter('sync_resolve')
        return {key: resolve_sync(provider)() for key, provider in self._providers.items()}