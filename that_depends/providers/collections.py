import typing

from that_depends.providers.base import AbstractProvider


T_co = typing.TypeVar("T_co", covariant=True)


class List(AbstractProvider[list[T_co]]):
    __slots__ = ("_providers",)

    def __init__(self, *providers: AbstractProvider[T_co]) -> None:
        super().__init__()
        self._providers: typing.Final = providers

    async def async_resolve(self) -> list[T_co]:
        return [await x.async_resolve() for x in self._providers]

    def sync_resolve(self) -> list[T_co]:
        return [x.sync_resolve() for x in self._providers]

    async def __call__(self) -> list[T_co]:
        return await self.async_resolve()

    def __getattr__(self, item: str) -> typing.Any:
        raise AttributeError(f"'List' object has no attribute '{item}'")


class Dict(AbstractProvider[dict[str, T_co]]):
    __slots__ = ("_providers",)

    def __init__(self, **providers: AbstractProvider[T_co]) -> None:
        super().__init__()
        self._providers: typing.Final = providers

    async def async_resolve(self) -> dict[str, T_co]:
        return {key: await provider.async_resolve() for key, provider in self._providers.items()}

    def sync_resolve(self) -> dict[str, T_co]:
        return {key: provider.sync_resolve() for key, provider in self._providers.items()}

    async def __call__(self) -> dict[str, T_co]:
        return await self.async_resolve()

    def __getattr__(self, item: str) -> typing.Any:
        raise AttributeError(f"'Dict' object has no attribute '{item}'")