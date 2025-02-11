import typing
from typing import TypeVar, Final, Callable, Awaitable, Dict, List
from that_depends.providers.base import AbstractProvider

T_co = TypeVar("T_co", covariant=True)

class List(AbstractProvider[List[T_co]]):
    __slots__ = ("_providers",)

    def __init__(self, *providers: AbstractProvider[T_co]) -> None:
        """
        Initialize the List provider with multiple providers.

        :param providers: Variable length provider list.
        """
        super().__init__()
        self._providers: Final = providers

    async def async_resolve(self) -> List[T_co]:
        return [await x.async_resolve() for x in self._providers]

    async def __call__(self) -> List[T_co]:
        return await self.async_resolve()

class Dict(AbstractProvider[Dict[str, T_co]]):
    __slots__ = ("_providers",)

    def __init__(self, **providers: AbstractProvider[T_co]) -> None:
        """
        Initialize the Dict provider with keyword providers.

        :param providers: Keyword arguments where keys are strings and values are providers.
        """
        super().__init__()
        self._providers: Final = providers

    async def async_resolve(self) -> Dict[str, T_co]:
        return {key: await provider.async_resolve() for key, provider in self._providers.items()}