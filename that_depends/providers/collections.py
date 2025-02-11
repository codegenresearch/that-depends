import typing
from typing import TypeVar, Final, Callable, Awaitable
from that_depends.providers.base import AbstractProvider

T_co = TypeVar("T_co", covariant=True)

class List(AbstractProvider[list[T_co]]):
    __slots__ = ("_providers",)

    def __init__(self, *providers: AbstractProvider[T_co]) -> None:
        """
        Initialize the List provider with multiple providers.

        :param providers: Variable length provider list.
        """
        super().__init__()
        self._providers: typing.Final = providers

    async def async_resolve(self) -> list[T_co]:
        return [await x.async_resolve() for x in self._providers]

    def sync_resolve(self) -> list[T_co]:
        return [x.sync_resolve() for x in self._providers]

    async def __call__(self) -> list[T_co]:
        return await self.async_resolve()

    def __getattr__(self, attr_name: str) -> typing.Any:  # noqa: ANN401
        raise AttributeError(f"'{type(self)}' object has no attribute '{attr_name}'")

class Dict(AbstractProvider[dict[str, T_co]]):
    __slots__ = ("_providers",)

    def __init__(self, **providers: AbstractProvider[T_co]) -> None:
        """
        Initialize the Dict provider with keyword providers.

        :param providers: Keyword arguments where keys are strings and values are providers.
        """
        super().__init__()
        self._providers: typing.Final = providers

    async def async_resolve(self) -> dict[str, T_co]:
        return {key: await provider.async_resolve() for key, provider in self._providers.items()}

    def sync_resolve(self) -> dict[str, T_co]:
        return {key: provider.sync_resolve() for key, provider in self._providers.items()}

    def __getattr__(self, attr_name: str) -> typing.Any:  # noqa: ANN401
        raise AttributeError(f"'{type(self)}' object has no attribute '{attr_name}'")